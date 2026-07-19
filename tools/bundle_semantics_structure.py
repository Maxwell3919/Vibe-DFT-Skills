#!/usr/bin/env python3
"""Deterministic semantic evaluators for the Wave 0 structure contracts.

The evaluator is deliberately side-effect free.  It consumes only the six
already-parsed bundle context mappings accepted by :mod:`bundle_semantics`.
It never opens a path, reparses raw bytes, imports code selected by record
content, or mutates the supplied views.  Raw-byte and artifact observations
must therefore arrive in authenticated envelopes from the bundle core.

``records_by_identity`` uses ``(contract_name, schema_version, record_id)``
tuple keys.  Record views use the dispatcher's eight-field identity wrapper.
Artifact views use its metadata wrapper plus ``parser_observations``.  Each
observation is emitted only by a fixed bundle-core parser after raw-byte hash
verification; it is never recovered by opening or reparsing an artifact here.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Any, Callable

CONTRACT_NAMES = (
    "structure-snapshot",
    "molecular-structure-manifest",
    "structure-transformation-manifest",
    "structure-export-manifest",
    "atomistic-trajectory-manifest",
)

_CONTEXT_FIELDS = frozenset(
    {
        "current_record",
        "current_record_index",
        "records_by_identity",
        "artifacts_by_label",
        "core_checks",
        "registry_snapshots",
    }
)
_RECORD_FIELDS = frozenset(
    {
        "contract_name",
        "schema_version",
        "record_id",
        "index",
        "data",
        "raw_sha256",
        "lifecycle",
        "integrity_verified_active",
    }
)
_ARTIFACT_FIELDS = frozenset(
    {
        "label",
        "index",
        "metadata",
        "raw_sha256",
        "bytes",
        "integrity_verified",
        "parser_observations",
    }
)
_RECORD_REF_FIELDS = frozenset(
    {"contract_name", "schema_version", "record_id", "sha256", "role"}
)
_ID_FIELDS = {
    "structure-snapshot": "snapshot_id",
    "molecular-structure-manifest": "molecular_structure_id",
    "structure-transformation-manifest": "transformation_id",
    "structure-export-manifest": "export_id",
    "atomistic-trajectory-manifest": "trajectory_id",
}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_LIFECYCLES = frozenset(
    {"blocked", "invalid", "planned", "revoked", "unsupported"}
)


SNAPSHOT_OBLIGATIONS = frozenset(
    {
        "structure-site-identity-not-unique",
        "structure-composition-site-mismatch",
        "structure-periodicity-cell-mismatch",
        "structure-coordinate-representation-mismatch",
        "structure-charge-spin-electron-parity-mismatch",
        "structure-identity-fingerprint-mismatch",
        "record-reference-dag-invalid",
    }
)
MOLECULAR_OBLIGATIONS = frozenset(
    {
        "molecular-snapshot-hash-mismatch",
        "molecular-site-reference-missing",
        "molecular-charge-multiplicity-electron-parity-mismatch",
        "molecular-connectivity-inconsistent",
        "molecular-fragment-coverage-inconsistent",
        "molecular-extraction-lineage-mismatch",
        "record-reference-dag-invalid",
    }
)
TRANSFORMATION_OBLIGATIONS = frozenset(
    {
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
    }
)
EXPORT_OBLIGATIONS = frozenset(
    {
        "structure-export-source-hash-mismatch",
        "structure-export-file-hash-mismatch",
        "structure-export-output-index-not-unique",
        "structure-export-atom-map-incomplete",
        "structure-export-unit-map-inconsistent",
        "structure-export-target-profile-mismatch",
        "structure-export-roundtrip-fingerprint-mismatch",
        "structure-export-loss-undisclosed",
        "record-reference-dag-invalid",
    }
)
TRAJECTORY_OBLIGATIONS = frozenset(
    {
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
    }
)
OBLIGATION_IDS = frozenset().union(
    SNAPSHOT_OBLIGATIONS,
    MOLECULAR_OBLIGATIONS,
    TRANSFORMATION_OBLIGATIONS,
    EXPORT_OBLIGATIONS,
    TRAJECTORY_OBLIGATIONS,
)


@dataclass(frozen=True)
class _Problem(Exception):
    status: str
    finding_codes: tuple[str, ...]
    location: str
    message: str


def _problem(status: str, code: str, location: str, message: str) -> _Problem:
    return _Problem(status, (code,), location, message)


def _fail(code: str, location: str, message: str) -> None:
    raise _problem("fail", code, location, message)


def _block(code: str, location: str, message: str) -> None:
    raise _problem("blocked", code, location, message)


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _json_digest(value: Any) -> str:
    raw = json.dumps(
        _plain(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _finite_number(value: Any, location: str) -> float:
    if not _is_number(value):
        _block(
            "STRUCTURE_NUMERIC_EVIDENCE_MISSING",
            location,
            "A finite numeric value is required for this semantic comparison.",
        )
    return float(value)


def _finite_vector(value: Any, length: int, location: str) -> tuple[float, ...]:
    if not isinstance(value, (list, tuple)) or len(value) != length:
        _block(
            "STRUCTURE_VECTOR_EVIDENCE_MISSING",
            location,
            f"A finite vector of length {length} is required.",
        )
    return tuple(
        _finite_number(item, f"{location}/{index}") for index, item in enumerate(value)
    )


def _matrix3(value: Any, location: str) -> tuple[tuple[float, ...], ...]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        _block(
            "STRUCTURE_CELL_EVIDENCE_MISSING",
            location,
            "A finite 3x3 cell matrix is required.",
        )
    return tuple(
        _finite_vector(row, 3, f"{location}/{index}") for index, row in enumerate(value)
    )


def _determinant(matrix: Sequence[Sequence[float]]) -> float:
    a, b, c = matrix
    return (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )


def _fractional_to_cartesian(
    fractional: Sequence[float], cell: Sequence[Sequence[float]]
) -> tuple[float, float, float]:
    return tuple(
        sum(fractional[row] * cell[row][column] for row in range(3))
        for column in range(3)
    )


def _max_residual(left: Sequence[float], right: Sequence[float]) -> float:
    return max(abs(a - b) for a, b in zip(left, right, strict=True))


def _record_identity(data: Mapping[str, Any]) -> tuple[str, str, str]:
    contract_name = data.get("contract_name")
    schema_version = data.get("schema_version")
    if not isinstance(contract_name, str) or not isinstance(schema_version, str):
        _block(
            "STRUCTURE_RECORD_IDENTITY_MISSING",
            "record",
            "A strictly parsed record lacks contract_name or schema_version.",
        )
    id_field = _ID_FIELDS.get(contract_name, "record_id")
    record_id = data.get(id_field)
    if not isinstance(record_id, str) or not record_id:
        _block(
            "STRUCTURE_RECORD_IDENTITY_MISSING",
            f"record/{id_field}",
            "A strictly parsed record lacks its declared top-level record ID.",
        )
    return contract_name, schema_version, record_id


def _validate_record_view(value: Any, location: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _RECORD_FIELDS:
        _block(
            "STRUCTURE_RECORD_VIEW_INVALID",
            location,
            "Record views must use the dispatcher's exact eight-field identity wrapper.",
        )
    if not isinstance(value["data"], Mapping):
        _block(
            "STRUCTURE_RECORD_VIEW_INVALID",
            f"{location}/data",
            "Record data must be a strictly parsed mapping.",
        )
    if not isinstance(value["raw_sha256"], str) or not _SHA256.fullmatch(
        value["raw_sha256"]
    ):
        _block(
            "STRUCTURE_RECORD_VIEW_INVALID",
            f"{location}/raw_sha256",
            "Record raw_sha256 must be the bundle core's lowercase SHA-256 observation.",
        )
    if not isinstance(value["index"], int) or isinstance(value["index"], bool):
        _block(
            "STRUCTURE_RECORD_VIEW_INVALID",
            f"{location}/index",
            "Record index must be an integer.",
        )
    if not isinstance(value["lifecycle"], str) or not isinstance(
        value["integrity_verified_active"], bool
    ):
        _block(
            "STRUCTURE_RECORD_VIEW_INVALID",
            location,
            "Record lifecycle and integrity status have invalid types.",
        )
    if (
        value["contract_name"],
        value["schema_version"],
        value["record_id"],
    ) != _record_identity(value["data"]):
        _block(
            "STRUCTURE_RECORD_VIEW_INVALID",
            location,
            "Record wrapper identity differs from strictly parsed record data.",
        )
    return value


def _validate_artifact_view(value: Any, location: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _ARTIFACT_FIELDS:
        _block(
            "STRUCTURE_ARTIFACT_VIEW_INVALID",
            location,
            "Artifact views must use the frozen semantic envelope.",
        )
    if not isinstance(value["label"], str) or not value["label"]:
        _block(
            "STRUCTURE_ARTIFACT_VIEW_INVALID",
            f"{location}/label",
            "Artifact label must be a nonempty string.",
        )
    if not isinstance(value["metadata"], Mapping):
        _block(
            "STRUCTURE_ARTIFACT_VIEW_INVALID",
            f"{location}/metadata",
            "Artifact metadata must be a path-free mapping.",
        )
    if not isinstance(value["parser_observations"], (list, tuple)):
        _block(
            "STRUCTURE_ARTIFACT_VIEW_INVALID",
            f"{location}/parser_observations",
            "Artifact parser_observations must be a frozen sequence.",
        )
    if not isinstance(value["raw_sha256"], str) or not _SHA256.fullmatch(
        value["raw_sha256"]
    ):
        _block(
            "STRUCTURE_ARTIFACT_VIEW_INVALID",
            f"{location}/raw_sha256",
            "Artifact raw_sha256 must be supplied by the bundle core.",
        )
    if not isinstance(value["bytes"], int) or value["bytes"] < 0:
        _block(
            "STRUCTURE_ARTIFACT_VIEW_INVALID",
            f"{location}/bytes",
            "Artifact byte count must be a nonnegative integer.",
        )
    if not isinstance(value["index"], int) or not isinstance(
        value["integrity_verified"], bool
    ):
        _block(
            "STRUCTURE_ARTIFACT_VIEW_INVALID",
            location,
            "Artifact index and integrity status have invalid types.",
        )
    return value


def _iter_record_refs(
    node: Any, path: tuple[str, ...] = ()
) -> Sequence[tuple[tuple[str, ...], Mapping[str, Any]]]:
    found: list[tuple[tuple[str, ...], Mapping[str, Any]]] = []
    if isinstance(node, Mapping):
        if frozenset(node) == _RECORD_REF_FIELDS:
            found.append((path, node))
        else:
            for key, value in node.items():
                found.extend(_iter_record_refs(value, (*path, str(key))))
    elif isinstance(node, (list, tuple)):
        for index, value in enumerate(node):
            found.extend(_iter_record_refs(value, (*path, str(index))))
    return found


def _pointer(parts: Sequence[str]) -> str:
    escaped = [part.replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(escaped) if escaped else "/"


class _State:
    def __init__(self, context: Mapping[str, Any]):
        if not isinstance(context, Mapping) or set(context) != _CONTEXT_FIELDS:
            _block(
                "STRUCTURE_SEMANTIC_CONTEXT_INVALID",
                "semantic-context",
                "Semantic context must contain exactly the six frozen dispatcher fields.",
            )
        current_index = context["current_record_index"]
        if not isinstance(current_index, int) or isinstance(current_index, bool):
            _block(
                "STRUCTURE_SEMANTIC_CONTEXT_INVALID",
                "semantic-context/current_record_index",
                "current_record_index must be an integer.",
            )
        for name in (
            "records_by_identity",
            "artifacts_by_label",
            "core_checks",
            "registry_snapshots",
        ):
            if not isinstance(context[name], Mapping):
                _block(
                    "STRUCTURE_SEMANTIC_CONTEXT_INVALID",
                    f"semantic-context/{name}",
                    f"{name} must be a read-only mapping.",
                )
        self.current = _validate_record_view(
            context["current_record"], "semantic-context/current_record"
        )
        if self.current["index"] != current_index:
            _block(
                "STRUCTURE_CURRENT_RECORD_INDEX_MISMATCH",
                "semantic-context/current_record_index",
                "The current record view and dispatcher index disagree.",
            )
        self.current_index = current_index
        self.data = self.current["data"]
        self.current_identity = _record_identity(self.data)
        self.records: dict[tuple[str, str, str], Mapping[str, Any]] = {}
        for key, view in context["records_by_identity"].items():
            checked = _validate_record_view(
                view, f"semantic-context/records_by_identity/{key!s}"
            )
            identity = _record_identity(checked["data"])
            if not isinstance(key, tuple) or len(key) != 3 or tuple(key) != identity:
                _block(
                    "STRUCTURE_RECORD_INDEX_IDENTITY_MISMATCH",
                    f"semantic-context/records_by_identity/{key!s}",
                    "The record index key does not match the strictly parsed record identity.",
                )
            if identity in self.records:
                _fail(
                    "DUPLICATE_RECORD_IDENTITY",
                    f"semantic-context/records_by_identity/{key!s}",
                    "A record identity occurs more than once.",
                )
            self.records[identity] = checked
        indexed_current = self.records.get(self.current_identity)
        if indexed_current is None or indexed_current["index"] != self.current_index:
            _block(
                "STRUCTURE_CURRENT_RECORD_NOT_INDEXED",
                "semantic-context/current_record",
                "The current record is absent from records_by_identity.",
            )
        self.artifacts = context["artifacts_by_label"]
        self.core_checks = context["core_checks"]
        self.registry = context["registry_snapshots"]

    def require_current_integrity(self) -> None:
        if (
            not self.current["integrity_verified_active"]
            or self.current["lifecycle"] != "active"
        ):
            _block(
                "STRUCTURE_CURRENT_RECORD_NOT_INTEGRITY_VERIFIED_ACTIVE",
                "semantic-context/current_record",
                "Domain semantics cannot pass for a record that is not integrity-verified and active.",
            )

    def resolve_ref(
        self,
        ref: Any,
        location: str,
        *,
        source_index: int | None = None,
    ) -> Mapping[str, Any]:
        if not isinstance(ref, Mapping) or frozenset(ref) != _RECORD_REF_FIELDS:
            _block(
                "RECORD_REF_TARGET_UNRESOLVED",
                location,
                "The reference is not a strictly parsed recordRef.",
            )
        identity = (
            ref.get("contract_name"),
            ref.get("schema_version"),
            ref.get("record_id"),
        )
        if not all(isinstance(part, str) and part for part in identity):
            _block(
                "RECORD_REF_TARGET_UNRESOLVED",
                location,
                "The reference identity is incomplete.",
            )
        target = self.records.get(identity)
        if target is None:
            _fail(
                "RECORD_REF_TARGET_UNRESOLVED",
                location,
                "The referenced record identity is absent from the bundle index.",
            )
        source = self.current_index if source_index is None else source_index
        if target["index"] >= source:
            code = (
                "RECORD_REF_SELF_REFERENCE"
                if target["index"] == source
                else "RECORD_REF_FORWARD_REFERENCE"
            )
            _fail(
                code,
                location,
                "A recordRef target must strictly precede its referrer.",
            )
        if ref.get("sha256") != target["raw_sha256"]:
            _fail(
                "RECORD_REF_RAW_SHA256_MISMATCH",
                f"{location}/sha256",
                "The declared digest does not match exact target raw bytes observed by the bundle core.",
            )
        if (
            not target["integrity_verified_active"]
            or target["lifecycle"] in _FORBIDDEN_LIFECYCLES
            or target["lifecycle"] != "active"
        ):
            _block(
                "RECORD_REF_TARGET_NOT_INTEGRITY_VERIFIED_ACTIVE",
                location,
                "The reference target is not integrity-verified and active.",
            )
        return target

    def artifact_for_ref(
        self, file_ref: Any, location: str, *, require_parsed: bool = False
    ) -> Mapping[str, Any]:
        if not isinstance(file_ref, Mapping):
            _block(
                "STRUCTURE_FILE_REF_INVALID",
                location,
                "The file reference is not a strictly parsed mapping.",
            )
        availability = file_ref.get("availability")
        if availability != "present":
            _block(
                "STRUCTURE_ARTIFACT_NOT_PRESENT",
                f"{location}/availability",
                "Artifact content is unavailable for deterministic semantic evaluation.",
            )
        label = file_ref.get("label")
        if not isinstance(label, str) or not label:
            _block(
                "STRUCTURE_FILE_REF_INVALID",
                f"{location}/label",
                "The file reference lacks a stable artifact label.",
            )
        view = self.artifacts.get(label)
        if view is None:
            _fail(
                "FILE_REF_ARTIFACT_UNRESOLVED",
                location,
                "The artifact label is absent from artifacts_by_label.",
            )
        checked = _validate_artifact_view(
            view, f"semantic-context/artifacts_by_label/{label}"
        )
        if checked["label"] != label:
            _block(
                "STRUCTURE_ARTIFACT_VIEW_INVALID",
                f"semantic-context/artifacts_by_label/{label}/label",
                "Artifact index key and wrapper label disagree.",
            )
        if not checked["integrity_verified"]:
            _block(
                "ARTIFACT_NOT_INTEGRITY_VERIFIED",
                location,
                "The artifact's raw hash, byte count, or inventory metadata was not verified.",
            )
        if file_ref.get("sha256") != checked["raw_sha256"]:
            _fail(
                "ARTIFACT_RAW_SHA256_MISMATCH",
                f"{location}/sha256",
                "The fileRef digest differs from the bundle core's raw-byte digest.",
            )
        if file_ref.get("bytes") != checked["bytes"]:
            _fail(
                "ARTIFACT_BYTES_MISMATCH",
                f"{location}/bytes",
                "The fileRef byte count differs from the bundle core observation.",
            )
        metadata = checked["metadata"]
        comparable = (
            "role",
            "label",
            "media_type",
            "format",
            "format_version",
            "availability",
            "sha256",
            "bytes",
            "sensitivity",
            "redistribution",
        )
        if any(file_ref.get(key) != metadata.get(key) for key in comparable):
            _fail(
                "FILE_REF_ARTIFACT_METADATA_MISMATCH",
                location,
                "The record fileRef differs from the path-free artifact inventory metadata.",
            )
        if not require_parsed:
            return checked
        successful: list[Mapping[str, Any]] = []
        required_observation_fields = {
            "parser_id",
            "parser_version",
            "parser_component_sha256",
            "source_raw_sha256",
            "status",
            "observations",
        }
        for index, observation in enumerate(checked["parser_observations"]):
            if (
                not isinstance(observation, Mapping)
                or set(observation) != required_observation_fields
            ):
                _block(
                    "STRUCTURE_PARSER_OBSERVATION_INVALID",
                    f"semantic-context/artifacts_by_label/{label}/parser_observations/{index}",
                    "A parser observation does not use the frozen bundle-core row shape.",
                )
            if (
                not isinstance(observation["parser_id"], str)
                or not observation["parser_id"]
                or not isinstance(observation["parser_version"], str)
                or not observation["parser_version"]
                or not isinstance(observation["parser_component_sha256"], str)
                or _SHA256.fullmatch(observation["parser_component_sha256"]) is None
                or observation["source_raw_sha256"] != checked["raw_sha256"]
                or observation["status"] not in {"pass", "fail", "blocked"}
            ):
                _block(
                    "STRUCTURE_PARSER_OBSERVATION_INVALID",
                    f"semantic-context/artifacts_by_label/{label}/parser_observations/{index}",
                    "Parser identity, component hash, source hash, or status is invalid.",
                )
            if observation["status"] == "pass" and isinstance(
                observation["observations"], Mapping
            ):
                successful.append(observation["observations"])
        if not successful:
            _block(
                "STRUCTURE_PARSED_ARTIFACT_EVIDENCE_MISSING",
                location,
                "The trusted bundle core supplied no parsed domain observation for this artifact.",
            )
        if len(successful) > 1:
            _block(
                "STRUCTURE_PARSED_ARTIFACT_EVIDENCE_AMBIGUOUS",
                location,
                "More than one successful parser observation is available for this artifact.",
            )
        return {**checked, "data": successful[0]}


def _sites(snapshot: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    value = snapshot.get("sites")
    if not isinstance(value, (list, tuple)) or not all(
        isinstance(site, Mapping) for site in value
    ):
        _block(
            "STRUCTURE_SITE_TABLE_MISSING",
            "/sites",
            "The strictly parsed structure lacks a usable site table.",
        )
    return tuple(value)


def _site_map(snapshot: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for index, site in enumerate(_sites(snapshot)):
        site_id = site.get("site_id")
        if not isinstance(site_id, str) or not site_id:
            _block(
                "STRUCTURE_SITE_ID_MISSING",
                f"/sites/{index}/site_id",
                "A site lacks a stable site_id.",
            )
        if site_id in result:
            _fail(
                "STRUCTURE_SITE_IDENTITY_NOT_UNIQUE",
                f"/sites/{index}/site_id",
                "site_id values must be unique.",
            )
        result[site_id] = site
    return result


def _cell(snapshot: Mapping[str, Any]) -> tuple[tuple[float, ...], ...]:
    cell = snapshot.get("cell")
    if not isinstance(cell, Mapping) or cell.get("status") != "present":
        _block(
            "STRUCTURE_CELL_EVIDENCE_MISSING",
            "/cell",
            "This comparison requires a present cell.",
        )
    return _matrix3(cell.get("vectors_ang"), "/cell/vectors_ang")


def _snapshot_precision(snapshot: Mapping[str, Any]) -> float:
    identity = snapshot.get("identity")
    if not isinstance(identity, Mapping):
        _block(
            "STRUCTURE_IDENTITY_EVIDENCE_MISSING",
            "/identity",
            "The structure identity declaration is missing.",
        )
    precision = _finite_number(
        identity.get("coordinate_precision_ang"),
        "/identity/coordinate_precision_ang",
    )
    if precision <= 0:
        _block(
            "STRUCTURE_IDENTITY_EVIDENCE_MISSING",
            "/identity/coordinate_precision_ang",
            "Coordinate precision must be positive.",
        )
    return precision


def _canonical_structure_digests(snapshot: Mapping[str, Any]) -> tuple[str, str]:
    precision = _snapshot_precision(snapshot)

    def ticks(value: Any, location: str) -> int:
        return int(round(_finite_number(value, location) / precision))

    cell = snapshot.get("cell")
    if not isinstance(cell, Mapping):
        _block(
            "STRUCTURE_IDENTITY_EVIDENCE_MISSING",
            "/cell",
            "Canonical structure payload requires the declared cell object.",
        )
    vectors = cell.get("vectors_ang")
    cell_ticks = None
    if vectors is not None:
        matrix = _matrix3(vectors, "/cell/vectors_ang")
        cell_ticks = [
            [
                ticks(item, f"/cell/vectors_ang/{row}/{column}")
                for column, item in enumerate(vector)
            ]
            for row, vector in enumerate(matrix)
        ]
    ordered = sorted(_sites(snapshot), key=lambda site: site.get("ordinal", -1))
    site_payload = []
    for index, site in enumerate(ordered):
        cart = _finite_vector(
            site.get("cartesian_ang"), 3, f"/sites/{index}/cartesian_ang"
        )
        site_payload.append(
            {
                "site_id": site.get("site_id"),
                "ordinal": site.get("ordinal"),
                "element": site.get("element"),
                "atomic_number": site.get("atomic_number"),
                "isotope": site.get("isotope"),
                "occupancy": site.get("occupancy"),
                "ordering_state": site.get("ordering_state"),
                "cartesian_ticks": [
                    ticks(value, f"/sites/{index}/cartesian_ang") for value in cart
                ],
                "formal_charge_e": site.get("formal_charge_e"),
                "magnetic_moment_mu_b": site.get("magnetic_moment_mu_b"),
            }
        )
    payload = {
        "canonicalization": "ordered-sites-cartesian-cell-v1",
        "precision_ang": precision,
        "structure_kind": snapshot.get("structure_kind"),
        "periodicity": _plain(snapshot.get("periodicity")),
        "cell_status": cell.get("status"),
        "cell_rank": cell.get("rank"),
        "cell_ticks": cell_ticks,
        "sites": site_payload,
    }
    site_order = [site.get("site_id") for site in ordered]
    return _json_digest(payload), _json_digest(site_order)


def _resolved_snapshot(
    state: _State, ref: Any, location: str
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    view = state.resolve_ref(ref, location)
    data = view["data"]
    if data.get("contract_name") != "structure-snapshot":
        _fail(
            "STRUCTURE_REFERENCE_TARGET_TYPE_MISMATCH",
            location,
            "The reference does not resolve to a structure snapshot.",
        )
    return view, data


def _snapshot_identity_not_unique(state: _State) -> None:
    sites = _sites(state.data)
    ids = [site.get("site_id") for site in sites]
    ordinals = [site.get("ordinal") for site in sites]
    if len(ids) != len(set(ids)):
        _fail(
            "STRUCTURE_SITE_IDENTITY_NOT_UNIQUE",
            "/sites",
            "site_id values are not unique.",
        )
    if any(not isinstance(value, str) or not value for value in ids):
        _fail(
            "STRUCTURE_SITE_IDENTITY_NOT_UNIQUE",
            "/sites",
            "Every site requires a nonempty site_id.",
        )
    if ordinals != list(range(len(sites))) or len(ordinals) != len(set(ordinals)):
        _fail(
            "STRUCTURE_SITE_ORDINAL_SEQUENCE_INVALID",
            "/sites",
            "Site ordinals must occur once in contiguous list order from zero.",
        )


def _hill_formula(counts: Mapping[str, int]) -> str:
    elements = sorted(counts)
    if "C" in counts:
        elements = (
            ["C"]
            + (["H"] if "H" in counts else [])
            + [item for item in elements if item not in {"C", "H"}]
        )
    return "".join(
        element + (str(counts[element]) if counts[element] != 1 else "")
        for element in elements
    )


def _snapshot_composition(state: _State) -> None:
    sites = _sites(state.data)
    site_counts = Counter(site.get("element") for site in sites)
    occupancy: dict[str, float] = defaultdict(float)
    for index, site in enumerate(sites):
        element = site.get("element")
        if not isinstance(element, str) or not element:
            _fail(
                "STRUCTURE_COMPOSITION_SITE_MISMATCH",
                f"/sites/{index}/element",
                "A site element is missing.",
            )
        occupancy[element] += _finite_number(
            site.get("occupancy"), f"/sites/{index}/occupancy"
        )
    composition = state.data.get("composition")
    if not isinstance(composition, Mapping) or not isinstance(
        composition.get("elements"), (list, tuple)
    ):
        _block(
            "STRUCTURE_COMPOSITION_EVIDENCE_MISSING",
            "/composition",
            "The declared composition table is missing.",
        )
    declared: dict[str, Mapping[str, Any]] = {}
    for index, item in enumerate(composition["elements"]):
        if not isinstance(item, Mapping) or not isinstance(item.get("element"), str):
            _block(
                "STRUCTURE_COMPOSITION_EVIDENCE_MISSING",
                f"/composition/elements/{index}",
                "A composition entry is malformed.",
            )
        if item["element"] in declared:
            _fail(
                "STRUCTURE_COMPOSITION_SITE_MISMATCH",
                f"/composition/elements/{index}/element",
                "Composition elements are duplicated.",
            )
        declared[item["element"]] = item
    if set(declared) != set(site_counts):
        _fail(
            "STRUCTURE_COMPOSITION_SITE_MISMATCH",
            "/composition/elements",
            "Declared and recomputed element sets differ.",
        )
    for element, count in site_counts.items():
        item = declared[element]
        if item.get("site_count") != count or not _is_number(item.get("occupancy_sum")):
            _fail(
                "STRUCTURE_COMPOSITION_SITE_MISMATCH",
                f"/composition/elements/{element}",
                "Declared site count or occupancy sum is inconsistent.",
            )
        if abs(float(item["occupancy_sum"]) - occupancy[element]) > 1.0e-10:
            _fail(
                "STRUCTURE_COMPOSITION_SITE_MISMATCH",
                f"/composition/elements/{element}/occupancy_sum",
                "Declared occupancy sum differs from the site table.",
            )
    if composition.get("formula") != _hill_formula(site_counts):
        _fail(
            "STRUCTURE_COMPOSITION_SITE_MISMATCH",
            "/composition/formula",
            "Formula differs from the recomputed Hill formula.",
        )


def _snapshot_periodicity(state: _State) -> None:
    periodicity = state.data.get("periodicity")
    cell = state.data.get("cell")
    if not isinstance(periodicity, Mapping) or not isinstance(cell, Mapping):
        _block(
            "STRUCTURE_PERIODICITY_EVIDENCE_MISSING",
            "/periodicity",
            "Periodicity and cell declarations are required.",
        )
    pbc = periodicity.get("pbc")
    if (
        not isinstance(pbc, (list, tuple))
        or len(pbc) != 3
        or not all(isinstance(item, bool) for item in pbc)
    ):
        _block(
            "STRUCTURE_PERIODICITY_EVIDENCE_MISSING",
            "/periodicity/pbc",
            "PBC must be a three-boolean vector.",
        )
    dimensions = sum(pbc)
    expected_boundary = {0: "isolated", 1: "wire-1d", 2: "slab-2d", 3: "periodic-3d"}[
        dimensions
    ]
    expected_kind_dimensions = {
        "isolated-molecule": 0,
        "isolated-cluster": 0,
        "periodic-wire": 1,
        "periodic-slab": 2,
        "periodic-crystal": 3,
    }
    if (
        periodicity.get("dimensions") != dimensions
        or periodicity.get("boundary_condition") != expected_boundary
        or expected_kind_dimensions.get(state.data.get("structure_kind")) != dimensions
    ):
        _fail(
            "STRUCTURE_PERIODICITY_CELL_MISMATCH",
            "/periodicity",
            "Structure kind, dimensions, PBC, and boundary condition disagree.",
        )
    if dimensions == 0:
        if (
            cell.get("status") != "not-applicable"
            or cell.get("rank") != 0
            or cell.get("vectors_ang") is not None
        ):
            _fail(
                "STRUCTURE_PERIODICITY_CELL_MISMATCH",
                "/cell",
                "An isolated structure must declare no cell.",
            )
        return
    matrix = _matrix3(cell.get("vectors_ang"), "/cell/vectors_ang")
    if cell.get("status") != "present" or cell.get("rank") != 3:
        _fail(
            "STRUCTURE_PERIODICITY_CELL_MISMATCH",
            "/cell",
            "A periodic structure requires a rank-three present cell.",
        )
    if abs(_determinant(matrix)) <= 1.0e-12:
        _fail(
            "STRUCTURE_PERIODICITY_CELL_MISMATCH",
            "/cell/vectors_ang",
            "The declared periodic cell is singular.",
        )


def _snapshot_coordinates(state: _State) -> None:
    periodicity = state.data.get("periodicity")
    if not isinstance(periodicity, Mapping):
        _block(
            "STRUCTURE_COORDINATE_EVIDENCE_MISSING",
            "/periodicity",
            "Periodicity is required to interpret coordinates.",
        )
    dimensions = periodicity.get("dimensions")
    tolerance = _snapshot_precision(state.data)
    if dimensions == 0:
        for index, site in enumerate(_sites(state.data)):
            if site.get("fractional") is not None:
                _fail(
                    "STRUCTURE_COORDINATE_REPRESENTATION_MISMATCH",
                    f"/sites/{index}/fractional",
                    "Isolated structures cannot claim fractional coordinates.",
                )
            _finite_vector(
                site.get("cartesian_ang"), 3, f"/sites/{index}/cartesian_ang"
            )
        return
    matrix = _cell(state.data)
    for index, site in enumerate(_sites(state.data)):
        fractional = _finite_vector(
            site.get("fractional"), 3, f"/sites/{index}/fractional"
        )
        cartesian = _finite_vector(
            site.get("cartesian_ang"), 3, f"/sites/{index}/cartesian_ang"
        )
        reconstructed = _fractional_to_cartesian(fractional, matrix)
        if _max_residual(reconstructed, cartesian) > tolerance:
            _fail(
                "STRUCTURE_COORDINATE_REPRESENTATION_MISMATCH",
                f"/sites/{index}",
                "Fractional and Cartesian coordinates disagree beyond the declared precision.",
            )


def _electron_count(snapshot: Mapping[str, Any]) -> int:
    total = 0
    for index, site in enumerate(_sites(snapshot)):
        occupancy = _finite_number(site.get("occupancy"), f"/sites/{index}/occupancy")
        if abs(occupancy - 1.0) > 1.0e-12:
            _block(
                "STRUCTURE_ELECTRON_COUNT_UNRESOLVED",
                f"/sites/{index}/occupancy",
                "Electron parity is unresolved for partial or disordered occupancy.",
            )
        atomic_number = site.get("atomic_number")
        if not isinstance(atomic_number, int) or isinstance(atomic_number, bool):
            _block(
                "STRUCTURE_ELECTRON_COUNT_UNRESOLVED",
                f"/sites/{index}/atomic_number",
                "Atomic numbers are required to derive electron count.",
            )
        total += atomic_number
    charge = snapshot.get("charge_state")
    if not isinstance(charge, Mapping) or charge.get("status") != "known":
        _block(
            "STRUCTURE_CHARGE_STATE_UNRESOLVED",
            "/charge_state",
            "A known net charge is required to derive electron parity.",
        )
    net_charge = _finite_number(
        charge.get("net_charge_e"), "/charge_state/net_charge_e"
    )
    electrons = total - net_charge
    rounded = round(electrons)
    if abs(electrons - rounded) > 1.0e-10 or rounded < 0:
        _fail(
            "STRUCTURE_CHARGE_SPIN_ELECTRON_PARITY_MISMATCH",
            "/charge_state/net_charge_e",
            "Nuclear charge minus net charge does not yield a nonnegative integer electron count.",
        )
    return int(rounded)


def _spin_compatible(electrons: int, multiplicity: int) -> bool:
    unpaired = multiplicity - 1
    return (
        multiplicity >= 1 and unpaired <= electrons and (electrons - unpaired) % 2 == 0
    )


def _snapshot_charge_spin(state: _State) -> None:
    electrons = _electron_count(state.data)
    spin = state.data.get("spin_state")
    if not isinstance(spin, Mapping) or spin.get("status") == "unknown":
        _block(
            "STRUCTURE_SPIN_STATE_UNRESOLVED",
            "/spin_state",
            "Spin state is unresolved.",
        )
    if spin.get("status") == "not-applicable":
        return
    multiplicity = spin.get("multiplicity")
    magnetization = spin.get("total_magnetization_mu_b")
    if isinstance(multiplicity, int) and not isinstance(multiplicity, bool):
        if not _spin_compatible(electrons, multiplicity):
            _fail(
                "STRUCTURE_CHARGE_SPIN_ELECTRON_PARITY_MISMATCH",
                "/spin_state/multiplicity",
                "Electron parity is incompatible with the declared multiplicity.",
            )
        return
    if _is_number(magnetization):
        absolute = abs(float(magnetization))
        rounded = round(absolute)
        if (
            abs(absolute - rounded) > 1.0e-8
            or rounded > electrons
            or (electrons - rounded) % 2
        ):
            _fail(
                "STRUCTURE_CHARGE_SPIN_ELECTRON_PARITY_MISMATCH",
                "/spin_state/total_magnetization_mu_b",
                "Electron parity is incompatible with the declared magnetization convention.",
            )
        return
    _block(
        "STRUCTURE_SPIN_STATE_UNRESOLVED",
        "/spin_state",
        "Known spin state lacks multiplicity or total magnetization evidence.",
    )


def _snapshot_identity(state: _State) -> None:
    identity = state.data.get("identity")
    if not isinstance(identity, Mapping):
        _block(
            "STRUCTURE_IDENTITY_EVIDENCE_MISSING",
            "/identity",
            "The structure identity declaration is missing.",
        )
    if (
        identity.get("algorithm") != "sha256-canonical-ordered-structure-v1"
        or identity.get("canonicalization") != "ordered-sites-cartesian-cell-v1"
    ):
        _block(
            "STRUCTURE_IDENTITY_ALGORITHM_UNSUPPORTED",
            "/identity",
            "The declared canonicalization algorithm is unsupported.",
        )
    structure_digest, site_digest = _canonical_structure_digests(state.data)
    if identity.get("value") != structure_digest:
        _fail(
            "STRUCTURE_IDENTITY_FINGERPRINT_MISMATCH",
            "/identity/value",
            "Recomputed canonical structure digest differs from identity.value.",
        )
    if identity.get("site_order_sha256") != site_digest:
        _fail(
            "STRUCTURE_SITE_ORDER_FINGERPRINT_MISMATCH",
            "/identity/site_order_sha256",
            "Recomputed site-order digest differs from the declaration.",
        )


def _check_all_record_refs(state: _State) -> None:
    check = state.core_checks.get("record-reference-dag")
    if not isinstance(check, Mapping):
        _block(
            "CORE_OBLIGATION_CHECK_MISSING",
            "core:record-reference-dag",
            "The bundle core did not supply the record-reference DAG check.",
        )
    status = check.get("status")
    codes = check.get("finding_codes")
    if (
        status not in {"pass", "fail", "blocked"}
        or not isinstance(codes, (list, tuple))
        or not all(isinstance(code, str) and code for code in codes)
    ):
        _block(
            "CORE_OBLIGATION_CHECK_INVALID",
            "core:record-reference-dag",
            "The bundle core supplied a malformed DAG result.",
        )
    if status != "pass":
        raise _Problem(
            status,
            tuple(sorted(set(codes))) or ("RECORD_REFERENCE_DAG_INVALID",),
            "core:record-reference-dag",
            "The bundle core did not establish an immutable record-reference DAG.",
        )
    edges: dict[int, set[int]] = defaultdict(set)
    for identity, view in state.records.items():
        source_index = view["index"]
        for parts, ref in _iter_record_refs(view["data"]):
            target = state.resolve_ref(
                ref,
                f"record:{identity[0]}:{identity[2]}{_pointer(parts)}",
                source_index=source_index,
            )
            edges[source_index].add(target["index"])
    visiting: set[int] = set()
    visited: set[int] = set()

    def visit(node: int) -> None:
        if node in visiting:
            _fail(
                "RECORD_REF_CYCLE",
                "semantic-context/records_by_identity",
                "The record-reference graph contains a cycle.",
            )
        if node in visited:
            return
        visiting.add(node)
        for target in edges.get(node, ()):
            visit(target)
        visiting.remove(node)
        visited.add(node)

    for node in edges:
        visit(node)


def _molecular_snapshot(state: _State) -> Mapping[str, Any]:
    _view, snapshot = _resolved_snapshot(
        state, state.data.get("snapshot_ref"), "/snapshot_ref"
    )
    return snapshot


def _molecular_snapshot_hash(state: _State) -> None:
    _molecular_snapshot(state)


def _molecular_site_references(state: _State) -> None:
    snapshot = _molecular_snapshot(state)
    site_ids = set(_site_map(snapshot))
    connectivity = state.data.get("connectivity")
    if not isinstance(connectivity, Mapping):
        _block(
            "MOLECULAR_CONNECTIVITY_EVIDENCE_MISSING",
            "/connectivity",
            "Connectivity data are missing.",
        )
    referenced: list[tuple[str, Any]] = []
    for bond_index, bond in enumerate(connectivity.get("bonds", ())):
        if isinstance(bond, Mapping):
            for site_index, site_id in enumerate(bond.get("site_ids", ())):
                referenced.append(
                    (f"/connectivity/bonds/{bond_index}/site_ids/{site_index}", site_id)
                )
    for fragment_index, fragment in enumerate(state.data.get("fragments", ())):
        if isinstance(fragment, Mapping):
            for site_index, site_id in enumerate(fragment.get("site_ids", ())):
                referenced.append(
                    (f"/fragments/{fragment_index}/site_ids/{site_index}", site_id)
                )
    for isotope_index, isotope in enumerate(state.data.get("isotopes", ())):
        if isinstance(isotope, Mapping):
            referenced.append(
                (f"/isotopes/{isotope_index}/site_id", isotope.get("site_id"))
            )
    for location, site_id in referenced:
        if site_id not in site_ids:
            _fail(
                "MOLECULAR_SITE_REFERENCE_MISSING",
                location,
                "A molecular site reference is absent from the resolved snapshot.",
            )
    constraints_by_id = {
        item.get("constraint_id"): item
        for item in snapshot.get("constraints", ())
        if isinstance(item, Mapping)
    }
    for index, constraint_ref in enumerate(state.data.get("constraints", ())):
        if not isinstance(constraint_ref, Mapping):
            _block(
                "MOLECULAR_CONSTRAINT_EVIDENCE_MISSING",
                f"/constraints/{index}",
                "A molecular constraint reference is malformed.",
            )
        _resolved_snapshot(
            state,
            constraint_ref.get("snapshot_ref"),
            f"/constraints/{index}/snapshot_ref",
        )
        if constraint_ref.get("constraint_id") not in constraints_by_id:
            _fail(
                "MOLECULAR_SITE_REFERENCE_MISSING",
                f"/constraints/{index}/constraint_id",
                "The referenced snapshot constraint does not exist.",
            )
    boundary = state.data.get("extraction_boundary")
    if not isinstance(boundary, Mapping):
        _block(
            "MOLECULAR_EXTRACTION_EVIDENCE_MISSING",
            "/extraction_boundary",
            "Extraction boundary data are missing.",
        )
    for field in ("created_site_ids", "capped_site_ids"):
        for index, site_id in enumerate(boundary.get(field, ())):
            if site_id not in site_ids:
                _fail(
                    "MOLECULAR_SITE_REFERENCE_MISSING",
                    f"/extraction_boundary/{field}/{index}",
                    "A created or capped site is absent from the molecular snapshot.",
                )
    parent_ref = boundary.get("parent_periodic_snapshot_ref")
    if parent_ref is not None:
        _view, parent = _resolved_snapshot(
            state, parent_ref, "/extraction_boundary/parent_periodic_snapshot_ref"
        )
        parent_ids = set(_site_map(parent))
        for index, site_id in enumerate(boundary.get("removed_site_ids", ())):
            if site_id not in parent_ids:
                _fail(
                    "MOLECULAR_SITE_REFERENCE_MISSING",
                    f"/extraction_boundary/removed_site_ids/{index}",
                    "A removed site is absent from the extraction parent.",
                )
    elif boundary.get("removed_site_ids"):
        _fail(
            "MOLECULAR_SITE_REFERENCE_MISSING",
            "/extraction_boundary/removed_site_ids",
            "Removed sites require a resolved parent snapshot.",
        )


def _known_integer_state(value: Any, location: str) -> int:
    if not isinstance(value, Mapping) or value.get("status") != "known":
        _block(
            "MOLECULAR_QUANTUM_STATE_UNRESOLVED",
            location,
            "A known integer quantum-state value is required.",
        )
    number = value.get("value")
    if not isinstance(number, int) or isinstance(number, bool):
        _block(
            "MOLECULAR_QUANTUM_STATE_UNRESOLVED",
            f"{location}/value",
            "The quantum-state value is not an integer.",
        )
    return number


def _molecular_quantum_parity(state: _State) -> None:
    snapshot = _molecular_snapshot(state)
    nuclear_charge = sum(site.get("atomic_number", 0) for site in _sites(snapshot))
    if not isinstance(nuclear_charge, int):
        _block(
            "MOLECULAR_ELECTRON_COUNT_UNRESOLVED",
            "/snapshot_ref",
            "Atomic numbers are required to derive molecular electron count.",
        )
    charge = _known_integer_state(state.data.get("net_charge"), "/net_charge")
    multiplicity = _known_integer_state(state.data.get("multiplicity"), "/multiplicity")
    electron_state = state.data.get("electron_count")
    if (
        not isinstance(electron_state, Mapping)
        or electron_state.get("status") != "known"
    ):
        _block(
            "MOLECULAR_ELECTRON_COUNT_UNRESOLVED",
            "/electron_count",
            "A known electron count is required.",
        )
    declared = electron_state.get("value")
    derived = nuclear_charge - charge
    if declared != derived or not _spin_compatible(derived, multiplicity):
        _fail(
            "MOLECULAR_CHARGE_MULTIPLICITY_ELECTRON_PARITY_MISMATCH",
            "/electron_count",
            "Nuclear charge, net charge, electron count, and multiplicity are inconsistent.",
        )
    for index, fragment in enumerate(state.data.get("fragments", ())):
        if not isinstance(fragment, Mapping):
            _block(
                "MOLECULAR_FRAGMENT_EVIDENCE_MISSING",
                f"/fragments/{index}",
                "A fragment declaration is malformed.",
            )
        fragment_charge = _known_integer_state(
            fragment.get("net_charge"), f"/fragments/{index}/net_charge"
        )
        fragment_mult = _known_integer_state(
            fragment.get("multiplicity"), f"/fragments/{index}/multiplicity"
        )
        site_map = _site_map(snapshot)
        try:
            fragment_electrons = (
                sum(
                    site_map[site_id]["atomic_number"]
                    for site_id in fragment.get("site_ids", ())
                )
                - fragment_charge
            )
        except (KeyError, TypeError):
            _block(
                "MOLECULAR_FRAGMENT_EVIDENCE_MISSING",
                f"/fragments/{index}/site_ids",
                "Fragment electron count cannot be derived from its site set.",
            )
        if not _spin_compatible(fragment_electrons, fragment_mult):
            _fail(
                "MOLECULAR_CHARGE_MULTIPLICITY_ELECTRON_PARITY_MISMATCH",
                f"/fragments/{index}",
                "A fragment multiplicity is incompatible with its electron count.",
            )


def _molecular_connectivity(state: _State) -> None:
    snapshot = _molecular_snapshot(state)
    sites = set(_site_map(snapshot))
    connectivity = state.data.get("connectivity")
    if not isinstance(connectivity, Mapping):
        _block(
            "MOLECULAR_CONNECTIVITY_EVIDENCE_MISSING",
            "/connectivity",
            "Connectivity data are missing.",
        )
    status = connectivity.get("status")
    bonds = connectivity.get("bonds")
    if not isinstance(bonds, (list, tuple)):
        _block(
            "MOLECULAR_CONNECTIVITY_EVIDENCE_MISSING",
            "/connectivity/bonds",
            "Connectivity bonds are missing.",
        )
    if status in {"absent", "unresolved"}:
        if bonds:
            _fail(
                "MOLECULAR_CONNECTIVITY_INCONSISTENT",
                "/connectivity/bonds",
                "Absent or unresolved connectivity cannot contain bonds.",
            )
        if status == "unresolved":
            _block(
                "MOLECULAR_CONNECTIVITY_UNRESOLVED",
                "/connectivity/status",
                "Connectivity is explicitly unresolved.",
            )
        return
    ids: set[str] = set()
    pairs: set[tuple[str, str]] = set()
    for index, bond in enumerate(bonds):
        if not isinstance(bond, Mapping):
            _block(
                "MOLECULAR_CONNECTIVITY_EVIDENCE_MISSING",
                f"/connectivity/bonds/{index}",
                "A bond declaration is malformed.",
            )
        bond_id = bond.get("bond_id")
        site_ids = bond.get("site_ids")
        if bond_id in ids or not isinstance(bond_id, str):
            _fail(
                "MOLECULAR_CONNECTIVITY_INCONSISTENT",
                f"/connectivity/bonds/{index}/bond_id",
                "Bond IDs must be unique.",
            )
        ids.add(bond_id)
        if not isinstance(site_ids, (list, tuple)) or len(site_ids) != 2:
            _fail(
                "MOLECULAR_CONNECTIVITY_INCONSISTENT",
                f"/connectivity/bonds/{index}/site_ids",
                "A bond must contain exactly two sites.",
            )
        left, right = site_ids
        if left == right or left not in sites or right not in sites:
            _fail(
                "MOLECULAR_CONNECTIVITY_INCONSISTENT",
                f"/connectivity/bonds/{index}/site_ids",
                "A bond must join two distinct existing sites.",
            )
        pair = tuple(sorted((left, right)))
        if pair in pairs:
            _fail(
                "MOLECULAR_CONNECTIVITY_INCONSISTENT",
                f"/connectivity/bonds/{index}/site_ids",
                "Unordered bond pairs must be unique.",
            )
        pairs.add(pair)
        source = bond.get("source")
        if status == "explicit" and source not in {"explicit", "source-record"}:
            _fail(
                "MOLECULAR_CONNECTIVITY_INCONSISTENT",
                f"/connectivity/bonds/{index}/source",
                "Explicit connectivity lacks explicit or source-record evidence.",
            )
        if status == "perceived" and source != "perceived":
            _fail(
                "MOLECULAR_CONNECTIVITY_INCONSISTENT",
                f"/connectivity/bonds/{index}/source",
                "Perceived connectivity must identify perceived bonds.",
            )
    if status == "perceived" and not isinstance(connectivity.get("backend"), Mapping):
        _block(
            "MOLECULAR_CONNECTIVITY_METHOD_EVIDENCE_MISSING",
            "/connectivity/backend",
            "Perceived connectivity requires backend identity evidence.",
        )


def _molecular_fragment_coverage(state: _State) -> None:
    snapshot = _molecular_snapshot(state)
    all_sites = set(_site_map(snapshot))
    fragments = state.data.get("fragments")
    if not isinstance(fragments, (list, tuple)) or not fragments:
        _block(
            "MOLECULAR_FRAGMENT_EVIDENCE_MISSING",
            "/fragments",
            "At least one fragment declaration is required for coverage validation.",
        )
    whole = [
        item
        for item in fragments
        if isinstance(item, Mapping) and item.get("role") == "whole-molecule"
    ]
    if len(whole) != 1 or set(whole[0].get("site_ids", ())) != all_sites:
        _fail(
            "MOLECULAR_FRAGMENT_COVERAGE_INCONSISTENT",
            "/fragments",
            "Exactly one whole-molecule fragment must cover every site.",
        )
    if len(whole[0].get("site_ids", ())) != len(set(whole[0].get("site_ids", ()))):
        _fail(
            "MOLECULAR_FRAGMENT_COVERAGE_INCONSISTENT",
            "/fragments",
            "Whole-molecule membership contains duplicates.",
        )
    global_charge = _known_integer_state(state.data.get("net_charge"), "/net_charge")
    global_mult = _known_integer_state(state.data.get("multiplicity"), "/multiplicity")
    if (
        _known_integer_state(whole[0].get("net_charge"), "/fragments/whole/net_charge")
        != global_charge
        or _known_integer_state(
            whole[0].get("multiplicity"), "/fragments/whole/multiplicity"
        )
        != global_mult
    ):
        _fail(
            "MOLECULAR_FRAGMENT_COVERAGE_INCONSISTENT",
            "/fragments",
            "Whole-molecule charge or multiplicity differs from the molecular declaration.",
        )
    parts = [
        item
        for item in fragments
        if isinstance(item, Mapping) and item.get("role") != "whole-molecule"
    ]
    if parts:
        seen: set[str] = set()
        total_charge = 0
        fragment_multiplicities: dict[str, int] = {}
        for index, fragment in enumerate(parts):
            members = fragment.get("site_ids")
            if not isinstance(members, (list, tuple)):
                _block(
                    "MOLECULAR_FRAGMENT_EVIDENCE_MISSING",
                    f"/fragments/{index}/site_ids",
                    "Fragment membership is missing.",
                )
            if len(members) != len(set(members)) or seen.intersection(members):
                _fail(
                    "MOLECULAR_FRAGMENT_COVERAGE_INCONSISTENT",
                    f"/fragments/{index}/site_ids",
                    "Partition fragments silently overlap or duplicate members.",
                )
            seen.update(members)
            total_charge += _known_integer_state(
                fragment.get("net_charge"), f"/fragments/{index}/net_charge"
            )
            fragment_id = fragment.get("fragment_id")
            if not isinstance(fragment_id, str):
                _block(
                    "MOLECULAR_FRAGMENT_EVIDENCE_MISSING",
                    f"/fragments/{index}/fragment_id",
                    "A partition fragment lacks a stable ID.",
                )
            fragment_multiplicities[fragment_id] = _known_integer_state(
                fragment.get("multiplicity"),
                f"/fragments/{index}/multiplicity",
            )
        if seen != all_sites or total_charge != global_charge:
            _fail(
                "MOLECULAR_FRAGMENT_COVERAGE_INCONSISTENT",
                "/fragments",
                "Partition fragments omit sites or have incompatible total charge.",
            )
        coupling_registry = state.registry.get("fragment_spin_couplings")
        coupling = (
            coupling_registry.get(state.data.get("molecular_structure_id"))
            if isinstance(coupling_registry, Mapping)
            else None
        )
        if (
            not isinstance(coupling, Mapping)
            or coupling.get("fragment_multiplicities") != fragment_multiplicities
            or coupling.get("molecular_multiplicity") != global_mult
        ):
            _block(
                "MOLECULAR_FRAGMENT_SPIN_COUPLING_UNRESOLVED",
                "registry_snapshots/fragment_spin_couplings",
                "Multiple fragment spins require an immutable coupling declaration consistent with the molecular multiplicity.",
            )


def _same_ref_identity(left: Any, right: Any) -> bool:
    if not isinstance(left, Mapping) or not isinstance(right, Mapping):
        return False
    return all(
        left.get(key) == right.get(key)
        for key in ("contract_name", "schema_version", "record_id")
    )


def _molecular_extraction_lineage(state: _State) -> None:
    boundary = state.data.get("extraction_boundary")
    if not isinstance(boundary, Mapping):
        _block(
            "MOLECULAR_EXTRACTION_EVIDENCE_MISSING",
            "/extraction_boundary",
            "Extraction boundary data are missing.",
        )
    kind = boundary.get("kind")
    if kind == "native-molecule":
        forbidden = (
            boundary.get("parent_periodic_snapshot_ref"),
            boundary.get("transformation_ref"),
            boundary.get("boundary_decision_ref"),
        )
        if any(item is not None for item in forbidden) or any(
            boundary.get(field)
            for field in ("created_site_ids", "removed_site_ids", "capped_site_ids")
        ):
            _fail(
                "MOLECULAR_EXTRACTION_LINEAGE_MISMATCH",
                "/extraction_boundary",
                "Native molecules cannot claim extraction lineage or boundary site changes.",
            )
        return
    transform_view = state.resolve_ref(
        boundary.get("transformation_ref"),
        "/extraction_boundary/transformation_ref",
    )
    transform = transform_view["data"]
    if transform.get("contract_name") != "structure-transformation-manifest":
        _fail(
            "MOLECULAR_EXTRACTION_LINEAGE_MISMATCH",
            "/extraction_boundary/transformation_ref",
            "Extraction transformation_ref targets the wrong contract.",
        )
    decision = state.resolve_ref(
        boundary.get("boundary_decision_ref"),
        "/extraction_boundary/boundary_decision_ref",
    )
    if decision["data"].get("contract_name") != "decision-record":
        _fail(
            "MOLECULAR_EXTRACTION_LINEAGE_MISMATCH",
            "/extraction_boundary/boundary_decision_ref",
            "Extraction boundary decision targets the wrong contract.",
        )
    parent_ref = boundary.get("parent_periodic_snapshot_ref")
    if kind == "cluster-from-periodic":
        _resolved_snapshot(
            state, parent_ref, "/extraction_boundary/parent_periodic_snapshot_ref"
        )
        if not any(
            _same_ref_identity(parent_ref, item)
            for item in transform.get("parents", ())
        ):
            _fail(
                "MOLECULAR_EXTRACTION_LINEAGE_MISMATCH",
                "/extraction_boundary/parent_periodic_snapshot_ref",
                "Extraction parent is absent from transformation parents.",
            )
    if not any(
        _same_ref_identity(state.data.get("snapshot_ref"), item)
        for item in transform.get("children", ())
    ):
        _fail(
            "MOLECULAR_EXTRACTION_LINEAGE_MISMATCH",
            "/snapshot_ref",
            "Molecular snapshot is absent from transformation children.",
        )
    actual: dict[str, set[str]] = {
        "created_site_ids": set(),
        "removed_site_ids": set(),
        "capped_site_ids": set(),
    }
    for mapping in transform.get("site_mapping", ()):
        if not isinstance(mapping, Mapping):
            continue
        relation = mapping.get("relation")
        if relation == "created" and isinstance(mapping.get("child_site_id"), str):
            actual["created_site_ids"].add(mapping["child_site_id"])
        elif relation == "removed" and isinstance(mapping.get("parent_site_id"), str):
            actual["removed_site_ids"].add(mapping["parent_site_id"])
        elif relation == "capped" and isinstance(mapping.get("child_site_id"), str):
            actual["capped_site_ids"].add(mapping["child_site_id"])
    for field, observed in actual.items():
        if set(boundary.get(field, ())) != observed:
            _fail(
                "MOLECULAR_EXTRACTION_LINEAGE_MISMATCH",
                f"/extraction_boundary/{field}",
                "Declared extraction site changes differ from transformation mappings.",
            )


def _transformation_snapshots(
    state: _State,
) -> tuple[
    dict[tuple[str, str, str], Mapping[str, Any]],
    dict[tuple[str, str, str], Mapping[str, Any]],
]:
    parents: dict[tuple[str, str, str], Mapping[str, Any]] = {}
    children: dict[tuple[str, str, str], Mapping[str, Any]] = {}
    for field, destination in (("parents", parents), ("children", children)):
        refs = state.data.get(field)
        if not isinstance(refs, (list, tuple)) or not refs:
            _block(
                "STRUCTURE_TRANSFORM_REFERENCE_EVIDENCE_MISSING",
                f"/{field}",
                "A transformation requires at least one resolved snapshot reference.",
            )
        for index, ref in enumerate(refs):
            _view, snapshot = _resolved_snapshot(state, ref, f"/{field}/{index}")
            identity = (
                ref.get("contract_name"),
                ref.get("schema_version"),
                ref.get("record_id"),
            )
            if identity in destination:
                _fail(
                    "STRUCTURE_TRANSFORM_REFERENCE_HASH_MISMATCH",
                    f"/{field}/{index}",
                    "The same parent or child snapshot identity is declared more than once.",
                )
            destination[identity] = snapshot
    if set(parents).intersection(children):
        _fail(
            "STRUCTURE_TRANSFORM_REFERENCE_HASH_MISMATCH",
            "/parents",
            "A snapshot cannot be both parent and child of the same immutable transformation record.",
        )
    return parents, children


def _transformation_reference_hashes(state: _State) -> None:
    _transformation_snapshots(state)
    for parts, ref in _iter_record_refs(state.data):
        state.resolve_ref(ref, _pointer(parts))


def _transformation_mapping_ids(state: _State) -> None:
    mappings = state.data.get("site_mapping")
    if not isinstance(mappings, (list, tuple)) or not mappings:
        _block(
            "STRUCTURE_TRANSFORM_MAPPING_EVIDENCE_MISSING",
            "/site_mapping",
            "Site mapping assertions are missing.",
        )
    seen: set[str] = set()
    for index, mapping in enumerate(mappings):
        if not isinstance(mapping, Mapping) or not isinstance(
            mapping.get("mapping_id"), str
        ):
            _block(
                "STRUCTURE_TRANSFORM_MAPPING_EVIDENCE_MISSING",
                f"/site_mapping/{index}",
                "A mapping lacks a stable mapping_id.",
            )
        if mapping["mapping_id"] in seen:
            _fail(
                "STRUCTURE_TRANSFORM_MAPPING_ID_NOT_UNIQUE",
                f"/site_mapping/{index}/mapping_id",
                "mapping_id values must be unique.",
            )
        seen.add(mapping["mapping_id"])


def _mapping_endpoint(
    state: _State,
    mapping: Mapping[str, Any],
    side: str,
    snapshots: Mapping[tuple[str, str, str], Mapping[str, Any]],
    location: str,
) -> tuple[Mapping[str, Any], str | None]:
    ref = mapping.get(f"{side}_ref")
    identity = None
    if isinstance(ref, Mapping):
        identity = (
            ref.get("contract_name"),
            ref.get("schema_version"),
            ref.get("record_id"),
        )
    if identity not in snapshots:
        _fail(
            "STRUCTURE_TRANSFORM_SITE_REFERENCE_MISSING",
            f"{location}/{side}_ref",
            f"Mapping {side}_ref is not a declared transformation {side} snapshot.",
        )
    state.resolve_ref(ref, f"{location}/{side}_ref")
    return snapshots[identity], mapping.get(f"{side}_site_id")


def _transformation_site_references(state: _State) -> None:
    parents, children = _transformation_snapshots(state)
    for index, mapping in enumerate(state.data.get("site_mapping", ())):
        if not isinstance(mapping, Mapping):
            _block(
                "STRUCTURE_TRANSFORM_MAPPING_EVIDENCE_MISSING",
                f"/site_mapping/{index}",
                "A site mapping is malformed.",
            )
        location = f"/site_mapping/{index}"
        parent, parent_site_id = _mapping_endpoint(
            state, mapping, "parent", parents, location
        )
        child, child_site_id = _mapping_endpoint(
            state, mapping, "child", children, location
        )
        relation = mapping.get("relation")
        if parent_site_id is not None and parent_site_id not in _site_map(parent):
            _fail(
                "STRUCTURE_TRANSFORM_SITE_REFERENCE_MISSING",
                f"{location}/parent_site_id",
                "Mapped parent site does not exist in the exact parent snapshot.",
            )
        if child_site_id is not None and child_site_id not in _site_map(child):
            _fail(
                "STRUCTURE_TRANSFORM_SITE_REFERENCE_MISSING",
                f"{location}/child_site_id",
                "Mapped child site does not exist in the exact child snapshot.",
            )
        if relation == "created" and parent_site_id is not None:
            _fail(
                "STRUCTURE_TRANSFORM_SITE_REFERENCE_MISSING",
                f"{location}/parent_site_id",
                "A created relation cannot name a parent site.",
            )
        if relation == "removed" and child_site_id is not None:
            _fail(
                "STRUCTURE_TRANSFORM_SITE_REFERENCE_MISSING",
                f"{location}/child_site_id",
                "A removed relation cannot name a child site.",
            )
        if relation not in {"created", "removed"} and (
            parent_site_id is None or child_site_id is None
        ):
            _fail(
                "STRUCTURE_TRANSFORM_SITE_REFERENCE_MISSING",
                location,
                "This mapping relation requires existing parent and child endpoints.",
            )


def _qualified_sites(
    snapshots: Mapping[tuple[str, str, str], Mapping[str, Any]],
) -> set[tuple[tuple[str, str, str], str]]:
    return {
        (identity, site_id)
        for identity, snapshot in snapshots.items()
        for site_id in _site_map(snapshot)
    }


def _transformation_mapping_coverage(state: _State) -> None:
    parents, children = _transformation_snapshots(state)
    required_parents = _qualified_sites(parents)
    required_children = _qualified_sites(children)
    covered_parents: set[tuple[tuple[str, str, str], str]] = set()
    covered_children: set[tuple[tuple[str, str, str], str]] = set()
    for index, mapping in enumerate(state.data.get("site_mapping", ())):
        if not isinstance(mapping, Mapping):
            _block(
                "STRUCTURE_TRANSFORM_MAPPING_EVIDENCE_MISSING",
                f"/site_mapping/{index}",
                "A site mapping is malformed.",
            )
        parent_ref = mapping.get("parent_ref")
        child_ref = mapping.get("child_ref")
        parent_identity = (
            (
                parent_ref.get("contract_name"),
                parent_ref.get("schema_version"),
                parent_ref.get("record_id"),
            )
            if isinstance(parent_ref, Mapping)
            else None
        )
        child_identity = (
            (
                child_ref.get("contract_name"),
                child_ref.get("schema_version"),
                child_ref.get("record_id"),
            )
            if isinstance(child_ref, Mapping)
            else None
        )
        parent_site = mapping.get("parent_site_id")
        child_site = mapping.get("child_site_id")
        if isinstance(parent_site, str) and parent_identity is not None:
            covered_parents.add((parent_identity, parent_site))
        if isinstance(child_site, str) and child_identity is not None:
            covered_children.add((child_identity, child_site))
    if covered_parents != required_parents:
        _fail(
            "STRUCTURE_TRANSFORM_MAPPING_COVERAGE_INCOMPLETE",
            "/site_mapping",
            "Parent sites are silently omitted or mappings invent parent endpoints.",
        )
    if covered_children != required_children:
        _fail(
            "STRUCTURE_TRANSFORM_MAPPING_COVERAGE_INCOMPLETE",
            "/site_mapping",
            "Child sites are silently omitted or mappings invent child endpoints.",
        )


def _transformation_relation_cardinality(state: _State) -> None:
    mappings = state.data.get("site_mapping")
    if not isinstance(mappings, (list, tuple)):
        _block(
            "STRUCTURE_TRANSFORM_MAPPING_EVIDENCE_MISSING",
            "/site_mapping",
            "Site mappings are missing.",
        )
    by_parent: dict[tuple[Any, Any], list[Mapping[str, Any]]] = defaultdict(list)
    by_child: dict[tuple[Any, Any], list[Mapping[str, Any]]] = defaultdict(list)
    for index, mapping in enumerate(mappings):
        if not isinstance(mapping, Mapping):
            _block(
                "STRUCTURE_TRANSFORM_MAPPING_EVIDENCE_MISSING",
                f"/site_mapping/{index}",
                "A site mapping is malformed.",
            )
        parent_ref = mapping.get("parent_ref")
        child_ref = mapping.get("child_ref")
        parent_key = (
            parent_ref.get("record_id") if isinstance(parent_ref, Mapping) else None,
            mapping.get("parent_site_id"),
        )
        child_key = (
            child_ref.get("record_id") if isinstance(child_ref, Mapping) else None,
            mapping.get("child_site_id"),
        )
        if mapping.get("parent_site_id") is not None:
            by_parent[parent_key].append(mapping)
        if mapping.get("child_site_id") is not None:
            by_child[child_key].append(mapping)
        relation = mapping.get("relation")
        parent_site = mapping.get("parent_site_id")
        child_site = mapping.get("child_site_id")
        if relation == "created" and not (
            parent_site is None and isinstance(child_site, str)
        ):
            _fail(
                "STRUCTURE_TRANSFORM_RELATION_CARDINALITY_MISMATCH",
                f"/site_mapping/{index}",
                "created requires a null parent and one child endpoint.",
            )
        if relation == "removed" and not (
            isinstance(parent_site, str) and child_site is None
        ):
            _fail(
                "STRUCTURE_TRANSFORM_RELATION_CARDINALITY_MISMATCH",
                f"/site_mapping/{index}",
                "removed requires one parent and a null child endpoint.",
            )
        if relation in {"same", "capped"} and not (
            isinstance(parent_site, str) and isinstance(child_site, str)
        ):
            _fail(
                "STRUCTURE_TRANSFORM_RELATION_CARDINALITY_MISMATCH",
                f"/site_mapping/{index}",
                f"{relation} requires one parent and one child endpoint.",
            )
        if relation in {"same", "capped"} and (
            len(by_parent[parent_key]) != 1 or len(by_child[child_key]) != 1
        ):
            _fail(
                "STRUCTURE_TRANSFORM_RELATION_CARDINALITY_MISMATCH",
                f"/site_mapping/{index}",
                f"{relation} must be a one-to-one relation assertion.",
            )
        if relation == "created" and len(by_child[child_key]) != 1:
            _fail(
                "STRUCTURE_TRANSFORM_RELATION_CARDINALITY_MISMATCH",
                f"/site_mapping/{index}",
                "A created child endpoint must be asserted exactly once.",
            )
        if relation == "removed" and len(by_parent[parent_key]) != 1:
            _fail(
                "STRUCTURE_TRANSFORM_RELATION_CARDINALITY_MISMATCH",
                f"/site_mapping/{index}",
                "A removed parent endpoint must be asserted exactly once.",
            )
    for index, mapping in enumerate(mappings):
        relation = mapping.get("relation")
        parent_ref = mapping.get("parent_ref")
        child_ref = mapping.get("child_ref")
        parent_key = (
            parent_ref.get("record_id") if isinstance(parent_ref, Mapping) else None,
            mapping.get("parent_site_id"),
        )
        child_key = (
            child_ref.get("record_id") if isinstance(child_ref, Mapping) else None,
            mapping.get("child_site_id"),
        )
        if relation == "replicated":
            if any(
                item.get("relation") != "replicated" for item in by_parent[parent_key]
            ):
                _fail(
                    "STRUCTURE_TRANSFORM_RELATION_CARDINALITY_MISMATCH",
                    f"/site_mapping/{index}",
                    "A replicated parent endpoint cannot mix incompatible relation classes.",
                )
            children = {
                (
                    (
                        item.get("child_ref", {}).get("record_id")
                        if isinstance(item.get("child_ref"), Mapping)
                        else None
                    ),
                    item.get("child_site_id"),
                )
                for item in by_parent[parent_key]
                if item.get("relation") == "replicated"
            }
            if len(children) < 2:
                _fail(
                    "STRUCTURE_TRANSFORM_RELATION_CARDINALITY_MISMATCH",
                    f"/site_mapping/{index}",
                    "replicated must establish one-to-many distinct child endpoints.",
                )
        elif relation == "split":
            if any(item.get("relation") != "split" for item in by_parent[parent_key]):
                _fail(
                    "STRUCTURE_TRANSFORM_RELATION_CARDINALITY_MISMATCH",
                    f"/site_mapping/{index}",
                    "A split parent endpoint cannot mix incompatible relation classes.",
                )
            children = {
                (
                    (
                        item.get("child_ref", {}).get("record_id")
                        if isinstance(item.get("child_ref"), Mapping)
                        else None
                    ),
                    item.get("child_site_id"),
                )
                for item in by_parent[parent_key]
                if item.get("relation") == "split"
            }
            if len(children) < 2:
                _fail(
                    "STRUCTURE_TRANSFORM_RELATION_CARDINALITY_MISMATCH",
                    f"/site_mapping/{index}",
                    "split must establish one-to-many distinct child endpoints.",
                )
        elif relation == "merged":
            if any(item.get("relation") != "merged" for item in by_child[child_key]):
                _fail(
                    "STRUCTURE_TRANSFORM_RELATION_CARDINALITY_MISMATCH",
                    f"/site_mapping/{index}",
                    "A merged child endpoint cannot mix incompatible relation classes.",
                )
            parents = {
                (
                    (
                        item.get("parent_ref", {}).get("record_id")
                        if isinstance(item.get("parent_ref"), Mapping)
                        else None
                    ),
                    item.get("parent_site_id"),
                )
                for item in by_child[child_key]
                if item.get("relation") == "merged"
            }
            if len(parents) < 2:
                _fail(
                    "STRUCTURE_TRANSFORM_RELATION_CARDINALITY_MISMATCH",
                    f"/site_mapping/{index}",
                    "merged must establish many-to-one distinct parent endpoints.",
                )


def _transformation_image_shifts(state: _State) -> None:
    parents, children = _transformation_snapshots(state)
    roundtrip = state.data.get("roundtrip")
    declared_tolerance = (
        roundtrip.get("tolerance_ang") if isinstance(roundtrip, Mapping) else None
    )
    for index, mapping in enumerate(state.data.get("site_mapping", ())):
        if not isinstance(mapping, Mapping):
            _block(
                "STRUCTURE_TRANSFORM_MAPPING_EVIDENCE_MISSING",
                f"/site_mapping/{index}",
                "A site mapping is malformed.",
            )
        shift = mapping.get("image_shift")
        if shift is None:
            if mapping.get("relation") in {"same", "replicated"}:
                _fail(
                    "STRUCTURE_TRANSFORM_IMAGE_SHIFT_INCONSISTENT",
                    f"/site_mapping/{index}/image_shift",
                    "same and replicated mappings require an explicit image shift.",
                )
            continue
        shift_vector = _finite_vector(shift, 3, f"/site_mapping/{index}/image_shift")
        parent_ref = mapping.get("parent_ref")
        child_ref = mapping.get("child_ref")
        parent_identity = (
            (
                parent_ref.get("contract_name"),
                parent_ref.get("schema_version"),
                parent_ref.get("record_id"),
            )
            if isinstance(parent_ref, Mapping)
            else None
        )
        child_identity = (
            (
                child_ref.get("contract_name"),
                child_ref.get("schema_version"),
                child_ref.get("record_id"),
            )
            if isinstance(child_ref, Mapping)
            else None
        )
        if parent_identity not in parents or child_identity not in children:
            _fail(
                "STRUCTURE_TRANSFORM_IMAGE_SHIFT_INCONSISTENT",
                f"/site_mapping/{index}",
                "Image-shift endpoints are not transformation snapshots.",
            )
        parent_snapshot = parents[parent_identity]
        child_snapshot = children[child_identity]
        parent_site = _site_map(parent_snapshot).get(mapping.get("parent_site_id"))
        child_site = _site_map(child_snapshot).get(mapping.get("child_site_id"))
        if parent_site is None or child_site is None:
            _fail(
                "STRUCTURE_TRANSFORM_IMAGE_SHIFT_INCONSISTENT",
                f"/site_mapping/{index}",
                "Image-shift endpoints do not resolve to sites.",
            )
        parent_cart = _finite_vector(
            parent_site.get("cartesian_ang"),
            3,
            f"/site_mapping/{index}/parent_cartesian",
        )
        child_cart = _finite_vector(
            child_site.get("cartesian_ang"), 3, f"/site_mapping/{index}/child_cartesian"
        )
        parent_cell_decl = parent_snapshot.get("cell")
        if not isinstance(parent_cell_decl, Mapping):
            _block(
                "STRUCTURE_TRANSFORM_IMAGE_SHIFT_EVIDENCE_MISSING",
                f"/site_mapping/{index}/parent_ref",
                "Parent cell declaration is missing.",
            )
        if parent_cell_decl.get("status") == "present":
            parent_cell = _cell(parent_snapshot)
            translated = tuple(
                parent_cart[column]
                + sum(shift_vector[row] * parent_cell[row][column] for row in range(3))
                for column in range(3)
            )
        else:
            if any(abs(value) > 0 for value in shift_vector):
                _fail(
                    "STRUCTURE_TRANSFORM_IMAGE_SHIFT_INCONSISTENT",
                    f"/site_mapping/{index}/image_shift",
                    "A nonperiodic mapping cannot use a nonzero periodic image shift.",
                )
            translated = parent_cart
        tolerance = max(
            _snapshot_precision(parent_snapshot),
            _snapshot_precision(child_snapshot),
            float(declared_tolerance) if _is_number(declared_tolerance) else 0.0,
        )
        if _max_residual(translated, child_cart) > tolerance:
            _fail(
                "STRUCTURE_TRANSFORM_IMAGE_SHIFT_INCONSISTENT",
                f"/site_mapping/{index}/image_shift",
                "The periodic image shift does not reconstruct the child Cartesian position.",
            )


def _typed_parameter_value(parameters: Any, name: str) -> Any:
    if not isinstance(parameters, (list, tuple)):
        return None
    matches = [
        item
        for item in parameters
        if isinstance(item, Mapping) and item.get("name") == name
    ]
    if len(matches) != 1:
        return None
    item = matches[0]
    fields = {
        "number": "number_value",
        "integer": "integer_value",
        "boolean": "boolean_value",
        "string": "string_value",
        "integer-vector3": "integer_vector3_value",
        "integer-matrix3": "integer_matrix3_value",
        "number-vector": "number_vector_value",
        "number-matrix3": "number_matrix3_value",
    }
    return item.get(fields.get(item.get("value_kind"), ""))


def _all_site_count(snapshots: Mapping[Any, Mapping[str, Any]]) -> int:
    return sum(len(_sites(snapshot)) for snapshot in snapshots.values())


def _composition_signature(snapshot: Mapping[str, Any]) -> Counter[str]:
    return Counter(site.get("element") for site in _sites(snapshot))


def _matrix_multiply(
    left: Sequence[Sequence[float]], right: Sequence[Sequence[float]]
) -> tuple[tuple[float, ...], ...]:
    return tuple(
        tuple(
            sum(left[row][k] * right[k][column] for k in range(3))
            for column in range(3)
        )
        for row in range(3)
    )


def _transformation_operation_semantics(state: _State) -> None:
    parents, children = _transformation_snapshots(state)
    operation = state.data.get("operation_class")
    parent_count = _all_site_count(parents)
    child_count = _all_site_count(children)
    relations = Counter(
        mapping.get("relation")
        for mapping in state.data.get("site_mapping", ())
        if isinstance(mapping, Mapping)
    )
    if operation == "merge" and len(parents) < 2:
        _fail(
            "STRUCTURE_TRANSFORM_OPERATION_SEMANTICS_MISMATCH",
            "/parents",
            "merge requires multiple parents.",
        )
    elif operation == "split" and len(children) < 2:
        _fail(
            "STRUCTURE_TRANSFORM_OPERATION_SEMANTICS_MISMATCH",
            "/children",
            "split requires multiple children.",
        )
    elif operation == "supercell":
        if len(parents) != 1 or len(children) != 1:
            _fail(
                "STRUCTURE_TRANSFORM_OPERATION_SEMANTICS_MISMATCH",
                "/parents",
                "supercell requires one parent and one child.",
            )
        matrix_value = _typed_parameter_value(
            state.data.get("parameters"), "supercell-matrix"
        )
        matrix = _matrix3(matrix_value, "/parameters/supercell-matrix")
        rounded = tuple(tuple(round(item) for item in row) for row in matrix)
        if any(
            abs(matrix[row][column] - rounded[row][column]) > 1.0e-12
            for row in range(3)
            for column in range(3)
        ):
            _fail(
                "STRUCTURE_TRANSFORM_OPERATION_SEMANTICS_MISMATCH",
                "/parameters/supercell-matrix",
                "Supercell matrix must be integral.",
            )
        multiplicity = abs(round(_determinant(rounded)))
        if multiplicity < 1 or child_count != parent_count * multiplicity:
            _fail(
                "STRUCTURE_TRANSFORM_OPERATION_SEMANTICS_MISMATCH",
                "/site_mapping",
                "Supercell determinant and site replication count disagree.",
            )
        parent_snapshot = next(iter(parents.values()))
        child_snapshot = next(iter(children.values()))
        expected_cell = _matrix_multiply(rounded, _cell(parent_snapshot))
        actual_cell = _cell(child_snapshot)
        tolerance = max(
            _snapshot_precision(parent_snapshot), _snapshot_precision(child_snapshot)
        )
        if (
            max(
                _max_residual(a, b)
                for a, b in zip(expected_cell, actual_cell, strict=True)
            )
            > tolerance
        ):
            _fail(
                "STRUCTURE_TRANSFORM_OPERATION_SEMANTICS_MISMATCH",
                "/children/0",
                "Supercell matrix does not reproduce the child cell.",
            )
    elif operation in {"add-sites", "interstitial", "adsorbate"}:
        if child_count <= parent_count or relations["created"] == 0:
            _fail(
                "STRUCTURE_TRANSFORM_OPERATION_SEMANTICS_MISMATCH",
                "/site_mapping",
                f"{operation} requires a positive created-site delta.",
            )
    elif operation in {"remove-sites", "defect", "extract-cluster"}:
        if child_count >= parent_count or relations["removed"] == 0:
            _fail(
                "STRUCTURE_TRANSFORM_OPERATION_SEMANTICS_MISMATCH",
                "/site_mapping",
                f"{operation} requires a positive removed-site delta.",
            )
    elif operation == "substitution":
        if child_count != parent_count or len(parents) != 1 or len(children) != 1:
            _fail(
                "STRUCTURE_TRANSFORM_OPERATION_SEMANTICS_MISMATCH",
                "/site_mapping",
                "substitution must preserve site count.",
            )
        if _composition_signature(
            next(iter(parents.values()))
        ) == _composition_signature(next(iter(children.values()))):
            _fail(
                "STRUCTURE_TRANSFORM_OPERATION_SEMANTICS_MISMATCH",
                "/children",
                "substitution must change composition.",
            )
    elif operation == "cap-sites":
        if relations["capped"] == 0 and relations["created"] == 0:
            _fail(
                "STRUCTURE_TRANSFORM_OPERATION_SEMANTICS_MISMATCH",
                "/site_mapping",
                "cap-sites requires capped or created boundary sites.",
            )
    elif operation == "slab":
        if not any(
            child.get("periodicity", {}).get("dimensions") == 2
            for child in children.values()
        ):
            _fail(
                "STRUCTURE_TRANSFORM_OPERATION_SEMANTICS_MISMATCH",
                "/children",
                "slab must produce a two-dimensional periodic child.",
            )
    elif operation == "reorder":
        if len(parents) != 1 or len(children) != 1 or parent_count != child_count:
            _fail(
                "STRUCTURE_TRANSFORM_OPERATION_SEMANTICS_MISMATCH",
                "/site_mapping",
                "reorder must preserve one structure and its total site count.",
            )
        parent_snapshot = next(iter(parents.values()))
        child_snapshot = next(iter(children.values()))
        parent_sites = _site_map(parent_snapshot)
        child_sites = _site_map(child_snapshot)
        if set(parent_sites) != set(child_sites) or _composition_signature(
            parent_snapshot
        ) != _composition_signature(child_snapshot):
            _fail(
                "STRUCTURE_TRANSFORM_OPERATION_SEMANTICS_MISMATCH",
                "/children",
                "reorder cannot add, remove, rename, or substitute sites.",
            )
        tolerance = max(
            _snapshot_precision(parent_snapshot), _snapshot_precision(child_snapshot)
        )
        for site_id in parent_sites:
            parent_cart = _finite_vector(
                parent_sites[site_id].get("cartesian_ang"), 3, f"/parents/{site_id}"
            )
            child_cart = _finite_vector(
                child_sites[site_id].get("cartesian_ang"), 3, f"/children/{site_id}"
            )
            if _max_residual(parent_cart, child_cart) > tolerance:
                _fail(
                    "STRUCTURE_TRANSFORM_OPERATION_SEMANTICS_MISMATCH",
                    "/children",
                    "reorder cannot change Cartesian geometry.",
                )
        if parent_snapshot.get("cell", {}).get("status") != child_snapshot.get(
            "cell", {}
        ).get("status"):
            _fail(
                "STRUCTURE_TRANSFORM_OPERATION_SEMANTICS_MISMATCH",
                "/children",
                "reorder cannot change cell presence.",
            )
        if parent_snapshot.get("cell", {}).get("status") == "present":
            if (
                max(
                    _max_residual(a, b)
                    for a, b in zip(
                        _cell(parent_snapshot), _cell(child_snapshot), strict=True
                    )
                )
                > tolerance
            ):
                _fail(
                    "STRUCTURE_TRANSFORM_OPERATION_SEMANTICS_MISMATCH",
                    "/children",
                    "reorder cannot change the cell.",
                )
    elif operation == "format-roundtrip":
        if parent_count != child_count or len(parents) != 1 or len(children) != 1:
            _fail(
                "STRUCTURE_TRANSFORM_OPERATION_SEMANTICS_MISMATCH",
                "/children",
                "format-roundtrip must preserve one structure's site count.",
            )
        roundtrip = state.data.get("roundtrip")
        if not isinstance(roundtrip, Mapping) or roundtrip.get(
            "classification"
        ) not in {"exact", "equivalent-with-tolerance"}:
            _block(
                "STRUCTURE_TRANSFORM_OPERATION_EVIDENCE_MISSING",
                "/roundtrip",
                "A usable format-roundtrip needs an exact or tolerance-equivalent comparison.",
            )
    elif operation not in {"merge", "split"}:
        _block(
            "STRUCTURE_TRANSFORM_OPERATION_HANDLER_NOT_IMPLEMENTED",
            "/operation_class",
            "This operation class has no deterministic observed-delta handler in the current structure evaluator.",
        )


def _snapshot_equivalence(
    source: Mapping[str, Any], comparison: Mapping[str, Any], tolerance: float
) -> tuple[float, float]:
    source_sites = _site_map(source)
    comparison_sites = _site_map(comparison)
    if set(source_sites) != set(comparison_sites):
        return math.inf, math.inf
    coordinate_residual = 0.0
    for site_id in source_sites:
        if source_sites[site_id].get("element") != comparison_sites[site_id].get(
            "element"
        ):
            return math.inf, math.inf
        left = _finite_vector(
            source_sites[site_id].get("cartesian_ang"), 3, f"source/{site_id}"
        )
        right = _finite_vector(
            comparison_sites[site_id].get("cartesian_ang"), 3, f"comparison/{site_id}"
        )
        coordinate_residual = max(coordinate_residual, _max_residual(left, right))
    source_cell = source.get("cell")
    comparison_cell = comparison.get("cell")
    if not isinstance(source_cell, Mapping) or not isinstance(comparison_cell, Mapping):
        _block(
            "STRUCTURE_ROUNDTRIP_EVIDENCE_MISSING",
            "/cell",
            "Roundtrip cell declarations are missing.",
        )
    if source_cell.get("status") != comparison_cell.get("status"):
        return coordinate_residual, math.inf
    cell_residual = 0.0
    if source_cell.get("status") == "present":
        left_cell = _matrix3(source_cell.get("vectors_ang"), "source/cell")
        right_cell = _matrix3(comparison_cell.get("vectors_ang"), "comparison/cell")
        cell_residual = max(
            _max_residual(a, b) for a, b in zip(left_cell, right_cell, strict=True)
        )
    return coordinate_residual, cell_residual


def _roundtrip_claim(
    source: Mapping[str, Any],
    comparison: Mapping[str, Any],
    classification: Any,
    tolerance: Any,
    loss_codes: Any,
    location: str,
) -> None:
    source_digest, source_order = _canonical_structure_digests(source)
    comparison_digest, comparison_order = _canonical_structure_digests(comparison)
    losses = list(loss_codes) if isinstance(loss_codes, (list, tuple)) else []
    if classification == "exact":
        if (
            tolerance != 0
            or losses
            or source_digest != comparison_digest
            or source_order != comparison_order
        ):
            _fail(
                "STRUCTURE_ROUNDTRIP_FINGERPRINT_MISMATCH",
                location,
                "Exact roundtrip requires identical canonical and site-order digests, zero tolerance, and no losses.",
            )
    elif classification == "equivalent-with-tolerance":
        if not _is_number(tolerance) or float(tolerance) <= 0 or losses:
            _fail(
                "STRUCTURE_TRANSFORM_TOLERANCE_UNVERIFIED",
                location,
                "Equivalent roundtrip requires a positive explicit tolerance and no loss codes.",
            )
        coordinate_residual, cell_residual = _snapshot_equivalence(
            source, comparison, float(tolerance)
        )
        if max(coordinate_residual, cell_residual) > float(tolerance):
            _fail(
                "STRUCTURE_ROUNDTRIP_FINGERPRINT_MISMATCH",
                location,
                "Roundtrip residuals exceed the declared Cartesian-angstrom tolerance.",
            )
    elif classification in {"lossy", "failed"}:
        if not losses:
            _fail(
                "STRUCTURE_ROUNDTRIP_FINGERPRINT_MISMATCH",
                location,
                "Lossy or failed roundtrip requires stable loss codes.",
            )
        if (
            classification == "lossy"
            and source_digest == comparison_digest
            and source_order == comparison_order
        ):
            _fail(
                "STRUCTURE_ROUNDTRIP_FINGERPRINT_MISMATCH",
                location,
                "A lossy classification is unsupported by identical fingerprints.",
            )
    elif classification == "not-assessed":
        _block(
            "STRUCTURE_ROUNDTRIP_NOT_ASSESSED",
            location,
            "Roundtrip fingerprint equivalence is explicitly not assessed.",
        )
    else:
        _block(
            "STRUCTURE_ROUNDTRIP_EVIDENCE_MISSING",
            location,
            "Roundtrip classification is missing or unsupported.",
        )


def _transformation_roundtrip(state: _State) -> None:
    parents, _children = _transformation_snapshots(state)
    if len(parents) != 1:
        _block(
            "STRUCTURE_ROUNDTRIP_SOURCE_AMBIGUOUS",
            "/parents",
            "Fingerprint roundtrip evaluation requires one unambiguous source parent.",
        )
    roundtrip = state.data.get("roundtrip")
    if not isinstance(roundtrip, Mapping):
        _block(
            "STRUCTURE_ROUNDTRIP_EVIDENCE_MISSING",
            "/roundtrip",
            "Roundtrip declaration is missing.",
        )
    comparison_ref = roundtrip.get("comparison_snapshot_ref")
    if comparison_ref is None:
        if roundtrip.get("classification") in {"not-assessed", "failed"}:
            _block(
                "STRUCTURE_ROUNDTRIP_NOT_ASSESSED",
                "/roundtrip",
                "No comparison snapshot is available.",
            )
        _fail(
            "STRUCTURE_TRANSFORM_ROUNDTRIP_FINGERPRINT_MISMATCH",
            "/roundtrip/comparison_snapshot_ref",
            "A positive roundtrip claim requires a comparison snapshot.",
        )
    _view, comparison = _resolved_snapshot(
        state, comparison_ref, "/roundtrip/comparison_snapshot_ref"
    )
    evidence = roundtrip.get("evidence_refs")
    if not isinstance(evidence, (list, tuple)) or not evidence:
        _block(
            "STRUCTURE_ROUNDTRIP_EVIDENCE_MISSING",
            "/roundtrip/evidence_refs",
            "Roundtrip comparison evidence is missing.",
        )
    for index, ref in enumerate(evidence):
        state.resolve_ref(ref, f"/roundtrip/evidence_refs/{index}")
    try:
        _roundtrip_claim(
            next(iter(parents.values())),
            comparison,
            roundtrip.get("classification"),
            roundtrip.get("tolerance_ang"),
            roundtrip.get("loss_codes"),
            "/roundtrip",
        )
    except _Problem as problem:
        if problem.status == "fail" and problem.finding_codes == (
            "STRUCTURE_ROUNDTRIP_FINGERPRINT_MISMATCH",
        ):
            raise _Problem(
                "fail",
                ("STRUCTURE_TRANSFORM_ROUNDTRIP_FINGERPRINT_MISMATCH",),
                problem.location,
                problem.message,
            )
        raise


def _transformation_tolerance(state: _State) -> None:
    parents, _children = _transformation_snapshots(state)
    if len(parents) != 1:
        _block(
            "STRUCTURE_ROUNDTRIP_SOURCE_AMBIGUOUS",
            "/parents",
            "Tolerance evaluation requires one source parent.",
        )
    roundtrip = state.data.get("roundtrip")
    if not isinstance(roundtrip, Mapping):
        _block(
            "STRUCTURE_ROUNDTRIP_EVIDENCE_MISSING",
            "/roundtrip",
            "Roundtrip declaration is missing.",
        )
    classification = roundtrip.get("classification")
    if classification == "exact":
        if roundtrip.get("tolerance_ang") != 0:
            _fail(
                "STRUCTURE_TRANSFORM_TOLERANCE_UNVERIFIED",
                "/roundtrip/tolerance_ang",
                "Exact comparison must use zero tolerance.",
            )
        try:
            _transformation_roundtrip(state)
        except _Problem as problem:
            if problem.status == "fail":
                raise _Problem(
                    "fail",
                    ("STRUCTURE_TRANSFORM_TOLERANCE_UNVERIFIED",),
                    problem.location,
                    "Exact zero-tolerance comparison was not established.",
                )
            raise
    elif classification == "equivalent-with-tolerance":
        tolerance = roundtrip.get("tolerance_ang")
        if not _is_number(tolerance) or float(tolerance) <= 0:
            _fail(
                "STRUCTURE_TRANSFORM_TOLERANCE_UNVERIFIED",
                "/roundtrip/tolerance_ang",
                "Equivalent comparison requires positive angstrom tolerance.",
            )
        try:
            _transformation_roundtrip(state)
        except _Problem as problem:
            if problem.status == "fail":
                raise _Problem(
                    "fail",
                    ("STRUCTURE_TRANSFORM_TOLERANCE_UNVERIFIED",),
                    problem.location,
                    "Observed coordinate or cell residuals exceed the declared tolerance.",
                )
            raise
    else:
        _block(
            "STRUCTURE_TRANSFORM_TOLERANCE_UNVERIFIED",
            "/roundtrip/classification",
            "No positive tolerance-based equivalence claim can be established.",
        )


def _export_source_snapshot(state: _State) -> Mapping[str, Any]:
    _view, snapshot = _resolved_snapshot(
        state, state.data.get("snapshot_ref"), "/snapshot_ref"
    )
    return snapshot


def _export_source_hashes(state: _State) -> None:
    _export_source_snapshot(state)
    previous_refs: list[Mapping[str, Any]] = [state.data.get("snapshot_ref")]
    transformations = state.data.get("transformation_refs")
    if not isinstance(transformations, (list, tuple)):
        _block(
            "STRUCTURE_EXPORT_ANCESTRY_EVIDENCE_MISSING",
            "/transformation_refs",
            "Transformation ancestry must be an ordered list.",
        )
    for index, ref in enumerate(transformations):
        view = state.resolve_ref(ref, f"/transformation_refs/{index}")
        transform = view["data"]
        if transform.get("contract_name") != "structure-transformation-manifest":
            _fail(
                "STRUCTURE_EXPORT_SOURCE_HASH_MISMATCH",
                f"/transformation_refs/{index}",
                "An export transformation reference targets the wrong contract.",
            )
        parents = transform.get("parents")
        children = transform.get("children")
        if not isinstance(parents, (list, tuple)) or not isinstance(
            children, (list, tuple)
        ):
            _block(
                "STRUCTURE_EXPORT_ANCESTRY_EVIDENCE_MISSING",
                f"/transformation_refs/{index}",
                "Transformation ancestry lacks parent or child references.",
            )
        matched = [
            parent
            for parent in parents
            if any(_same_ref_identity(parent, previous) for previous in previous_refs)
        ]
        if not matched:
            _fail(
                "STRUCTURE_EXPORT_SOURCE_HASH_MISMATCH",
                f"/transformation_refs/{index}/parents",
                "Transformation ancestry is disconnected from the export source chain.",
            )
        for parts, nested_ref in _iter_record_refs(transform):
            state.resolve_ref(
                nested_ref,
                f"/transformation_refs/{index}/resolved{_pointer(parts)}",
                source_index=view["index"],
            )
        previous_refs = list(children)


def _export_files(
    state: _State, *, require_parsed: bool = False
) -> tuple[Mapping[str, Any], ...]:
    files = state.data.get("export_files")
    if not isinstance(files, (list, tuple)) or not files:
        _block(
            "STRUCTURE_EXPORT_FILE_EVIDENCE_MISSING",
            "/export_files",
            "At least one export file is required.",
        )
    return tuple(
        state.artifact_for_ref(
            file_ref, f"/export_files/{index}", require_parsed=require_parsed
        )
        for index, file_ref in enumerate(files)
    )


def _export_file_hashes(state: _State) -> None:
    _export_files(state)


def _export_parsed(state: _State) -> Mapping[str, Any]:
    candidates = [
        view["data"]
        for view in _export_files(state, require_parsed=True)
        if isinstance(view["data"], Mapping) and "atom_count" in view["data"]
    ]
    if len(candidates) != 1:
        _block(
            "STRUCTURE_EXPORT_PARSED_OUTPUT_AMBIGUOUS",
            "/export_files",
            "Exactly one authenticated export artifact must carry parsed atom-order evidence.",
        )
    return candidates[0]


def _export_output_indices(state: _State) -> None:
    parsed = _export_parsed(state)
    atom_count = parsed.get("atom_count")
    if not isinstance(atom_count, int) or atom_count < 1:
        _block(
            "STRUCTURE_EXPORT_PARSED_OUTPUT_MISSING",
            "/export_files/parsed/atom_count",
            "Parsed output atom count is unavailable.",
        )
    mapping = state.data.get("atom_order_mapping")
    if not isinstance(mapping, (list, tuple)):
        _block(
            "STRUCTURE_EXPORT_ATOM_MAP_EVIDENCE_MISSING",
            "/atom_order_mapping",
            "Atom order mapping is missing.",
        )
    indices = [
        item.get("output_index") if isinstance(item, Mapping) else None
        for item in mapping
    ]
    if indices != list(range(atom_count)) or len(indices) != len(set(indices)):
        _fail(
            "STRUCTURE_EXPORT_OUTPUT_INDEX_NOT_UNIQUE",
            "/atom_order_mapping",
            "output_index values are not unique and contiguous over parsed atoms.",
        )


def _export_atom_map(state: _State) -> None:
    source = _export_source_snapshot(state)
    source_ids = set(_site_map(source))
    parsed = _export_parsed(state)
    atom_count = parsed.get("atom_count")
    mapping = state.data.get("atom_order_mapping")
    if not isinstance(atom_count, int) or not isinstance(mapping, (list, tuple)):
        _block(
            "STRUCTURE_EXPORT_ATOM_MAP_EVIDENCE_MISSING",
            "/atom_order_mapping",
            "Parsed atom count or atom map is missing.",
        )
    output_indices: set[int] = set()
    mapped_sources: list[str] = []
    for index, item in enumerate(mapping):
        if not isinstance(item, Mapping):
            _block(
                "STRUCTURE_EXPORT_ATOM_MAP_EVIDENCE_MISSING",
                f"/atom_order_mapping/{index}",
                "An atom mapping entry is malformed.",
            )
        output_index = item.get("output_index")
        source_site = item.get("source_site_id")
        if not isinstance(output_index, int) or output_index in output_indices:
            _fail(
                "STRUCTURE_EXPORT_ATOM_MAP_INCOMPLETE",
                f"/atom_order_mapping/{index}/output_index",
                "Each parsed output atom must be mapped exactly once.",
            )
        if source_site not in source_ids:
            _fail(
                "STRUCTURE_EXPORT_ATOM_MAP_INCOMPLETE",
                f"/atom_order_mapping/{index}/source_site_id",
                "An atom map names a nonexistent source site.",
            )
        output_indices.add(output_index)
        mapped_sources.append(source_site)
    if output_indices != set(range(atom_count)):
        _fail(
            "STRUCTURE_EXPORT_ATOM_MAP_INCOMPLETE",
            "/atom_order_mapping",
            "The atom map does not cover every parsed output atom.",
        )
    roundtrip = state.data.get("roundtrip_validation")
    losses = (
        set(roundtrip.get("loss_codes", ()))
        if isinstance(roundtrip, Mapping)
        else set()
    )
    duplicate_sources = {
        source_site
        for source_site, count in Counter(mapped_sources).items()
        if count > 1
    }
    omitted_sources = source_ids.difference(mapped_sources)
    if duplicate_sources or omitted_sources:
        transformations = state.data.get("transformation_refs")
        if (
            not losses
            or not isinstance(transformations, (list, tuple))
            or not transformations
        ):
            _fail(
                "STRUCTURE_EXPORT_ATOM_MAP_INCOMPLETE",
                "/atom_order_mapping",
                "Source omissions or duplications lack transformation lineage and stable loss codes.",
            )
        justified_omissions: set[str] = set()
        justified_duplicates: set[str] = set()
        for index, ref in enumerate(transformations):
            view = state.resolve_ref(ref, f"/transformation_refs/{index}")
            transform = view["data"]
            if transform.get("contract_name") != "structure-transformation-manifest":
                _fail(
                    "STRUCTURE_EXPORT_ATOM_MAP_INCOMPLETE",
                    f"/transformation_refs/{index}",
                    "Atom-map lineage targets a non-transformation record.",
                )
            for mapping_entry in transform.get("site_mapping", ()):
                if not isinstance(mapping_entry, Mapping):
                    continue
                relation = mapping_entry.get("relation")
                source_site = mapping_entry.get("parent_site_id")
                if relation == "removed" and isinstance(source_site, str):
                    justified_omissions.add(source_site)
                if relation in {"replicated", "split"} and isinstance(source_site, str):
                    justified_duplicates.add(source_site)
        if not omitted_sources.issubset(
            justified_omissions
        ) or not duplicate_sources.issubset(justified_duplicates):
            _fail(
                "STRUCTURE_EXPORT_ATOM_MAP_INCOMPLETE",
                "/atom_order_mapping",
                "Transformation relations do not justify every omitted or duplicated source site.",
            )


def _export_tolerance(state: _State, source: Mapping[str, Any]) -> float:
    roundtrip = state.data.get("roundtrip_validation")
    value = roundtrip.get("tolerance_ang") if isinstance(roundtrip, Mapping) else None
    if value is None:
        return _snapshot_precision(source)
    if not _is_number(value) or float(value) < 0:
        _block(
            "STRUCTURE_EXPORT_TOLERANCE_MISSING",
            "/roundtrip_validation/tolerance_ang",
            "Export comparison tolerance is unavailable.",
        )
    return max(float(value), _snapshot_precision(source))


def _export_unit_mapping(state: _State) -> None:
    source = _export_source_snapshot(state)
    parsed = _export_parsed(state)
    unit_mapping = state.data.get("unit_mapping")
    if not isinstance(unit_mapping, Mapping):
        _block(
            "STRUCTURE_EXPORT_UNIT_EVIDENCE_MISSING",
            "/unit_mapping",
            "Unit mapping is missing.",
        )
    factor = _finite_number(
        unit_mapping.get("conversion_factor"), "/unit_mapping/conversion_factor"
    )
    if factor <= 0 or unit_mapping.get("input_length_unit") != "angstrom":
        _fail(
            "STRUCTURE_EXPORT_UNIT_MAP_INCONSISTENT",
            "/unit_mapping",
            "Input unit must be angstrom and conversion factor must be positive.",
        )
    if parsed.get("length_unit") != unit_mapping.get("output_length_unit"):
        _fail(
            "STRUCTURE_EXPORT_UNIT_MAP_INCONSISTENT",
            "/export_files/parsed/length_unit",
            "Parsed target unit differs from the declared output unit.",
        )
    coordinates = parsed.get("cartesian_coordinates")
    mapping = state.data.get("atom_order_mapping")
    if (
        not isinstance(coordinates, (list, tuple))
        or not isinstance(mapping, (list, tuple))
        or len(coordinates) != len(mapping)
    ):
        _block(
            "STRUCTURE_EXPORT_UNIT_EVIDENCE_MISSING",
            "/export_files/parsed/cartesian_coordinates",
            "Normalized parsed Cartesian coordinates are missing.",
        )
    source_sites = _site_map(source)
    tolerance = _export_tolerance(state, source) * factor
    for item in mapping:
        output_index = item.get("output_index")
        source_site = source_sites.get(item.get("source_site_id"))
        if not isinstance(output_index, int) or source_site is None:
            _block(
                "STRUCTURE_EXPORT_UNIT_EVIDENCE_MISSING",
                "/atom_order_mapping",
                "Atom mapping cannot drive unit comparison.",
            )
        expected = tuple(
            value * factor
            for value in _finite_vector(
                source_site.get("cartesian_ang"), 3, "/source/cartesian"
            )
        )
        observed = _finite_vector(
            coordinates[output_index],
            3,
            f"/export_files/parsed/cartesian_coordinates/{output_index}",
        )
        if _max_residual(expected, observed) > tolerance:
            _fail(
                "STRUCTURE_EXPORT_UNIT_MAP_INCONSISTENT",
                f"/export_files/parsed/cartesian_coordinates/{output_index}",
                "Converted source coordinates do not reproduce parsed export coordinates.",
            )
    if source.get("cell", {}).get("status") == "present":
        observed_cell = _matrix3(
            parsed.get("cell_vectors"), "/export_files/parsed/cell_vectors"
        )
        expected_cell = tuple(
            tuple(value * factor for value in row) for row in _cell(source)
        )
        if (
            max(
                _max_residual(a, b)
                for a, b in zip(expected_cell, observed_cell, strict=True)
            )
            > tolerance
        ):
            _fail(
                "STRUCTURE_EXPORT_UNIT_MAP_INCONSISTENT",
                "/export_files/parsed/cell_vectors",
                "Converted source cell does not reproduce the parsed export cell.",
            )


def _export_profiles(state: _State) -> Mapping[str, Any]:
    profiles = state.registry.get("structure_export_profiles")
    if not isinstance(profiles, Mapping):
        contracts = state.registry.get("domain_payload_contracts")
        profiles = (
            contracts.get("structure_export_profiles")
            if isinstance(contracts, Mapping)
            else None
        )
    if not isinstance(profiles, Mapping):
        _block(
            "STRUCTURE_EXPORT_PROFILE_REGISTRY_MISSING",
            "registry_snapshots/structure_export_profiles",
            "An immutable structure-export profile registry snapshot is required.",
        )
    return profiles


def _export_target_profile(state: _State) -> None:
    parsed = _export_parsed(state)
    profiles = _export_profiles(state)
    profile_id = state.data.get("code_profile_id")
    profile = profiles.get(profile_id)
    if not isinstance(profile, Mapping):
        _block(
            "STRUCTURE_EXPORT_TARGET_PROFILE_MISSING",
            "/code_profile_id",
            "The declared code profile is absent from the registry snapshot.",
        )
    target = state.data.get("target")
    if not isinstance(target, Mapping):
        _block(
            "STRUCTURE_EXPORT_TARGET_EVIDENCE_MISSING",
            "/target",
            "Export target declaration is missing.",
        )
    fields = (
        "format",
        "target_code",
        "coordinate_representation",
        "cell_representation",
    )
    for field in fields:
        if profile.get(field) != target.get(field) or parsed.get(field) != target.get(
            field
        ):
            _fail(
                "STRUCTURE_EXPORT_TARGET_PROFILE_MISMATCH",
                f"/target/{field}",
                "Manifest, parsed target, and registered code profile disagree.",
            )
    labels = parsed.get("atom_labels")
    pattern = profile.get("atom_label_pattern")
    if not isinstance(labels, (list, tuple)) or not isinstance(pattern, str):
        _block(
            "STRUCTURE_EXPORT_TARGET_PROFILE_MISSING",
            "/export_files/parsed/atom_labels",
            "Parsed labels or registered label grammar is missing.",
        )
    try:
        compiled = re.compile(pattern)
    except re.error:
        _block(
            "STRUCTURE_EXPORT_TARGET_PROFILE_INVALID",
            "registry_snapshots/structure_export_profiles",
            "Registered atom-label grammar is invalid.",
        )
    if any(
        not isinstance(label, str) or compiled.fullmatch(label) is None
        for label in labels
    ):
        _fail(
            "STRUCTURE_EXPORT_TARGET_PROFILE_MISMATCH",
            "/export_files/parsed/atom_labels",
            "Parsed atom labels violate the registered target profile.",
        )


def _export_roundtrip(state: _State) -> None:
    source = _export_source_snapshot(state)
    roundtrip = state.data.get("roundtrip_validation")
    if not isinstance(roundtrip, Mapping):
        _block(
            "STRUCTURE_EXPORT_ROUNDTRIP_EVIDENCE_MISSING",
            "/roundtrip_validation",
            "Export roundtrip declaration is missing.",
        )
    reconstructed_ref = roundtrip.get("reconstructed_snapshot_ref")
    if reconstructed_ref is None:
        _block(
            "STRUCTURE_EXPORT_ROUNDTRIP_EVIDENCE_MISSING",
            "/roundtrip_validation/reconstructed_snapshot_ref",
            "Re-imported structure snapshot is unavailable.",
        )
    _view, reconstructed = _resolved_snapshot(
        state,
        reconstructed_ref,
        "/roundtrip_validation/reconstructed_snapshot_ref",
    )
    evidence = roundtrip.get("evidence_refs")
    if not isinstance(evidence, (list, tuple)) or not evidence:
        _block(
            "STRUCTURE_EXPORT_ROUNDTRIP_EVIDENCE_MISSING",
            "/roundtrip_validation/evidence_refs",
            "Roundtrip evidence references are missing.",
        )
    for index, ref in enumerate(evidence):
        state.resolve_ref(ref, f"/roundtrip_validation/evidence_refs/{index}")
    try:
        _roundtrip_claim(
            source,
            reconstructed,
            roundtrip.get("classification"),
            roundtrip.get("tolerance_ang"),
            roundtrip.get("loss_codes"),
            "/roundtrip_validation",
        )
    except _Problem as problem:
        if problem.status == "fail" and problem.finding_codes == (
            "STRUCTURE_ROUNDTRIP_FINGERPRINT_MISMATCH",
        ):
            raise _Problem(
                "fail",
                ("STRUCTURE_EXPORT_ROUNDTRIP_FINGERPRINT_MISMATCH",),
                problem.location,
                problem.message,
            )
        raise


def _source_features(snapshot: Mapping[str, Any]) -> set[str]:
    features = {"labels", "precision", "site-identity"}
    if snapshot.get("cell", {}).get("status") == "present":
        features.add("cell")
    if snapshot.get("constraints"):
        features.add("constraints")
    if any(site.get("occupancy") != 1 for site in _sites(snapshot)):
        features.add("occupancy")
    if any(site.get("ordering_state") == "disordered" for site in _sites(snapshot)):
        features.add("disorder")
    return features


def _export_losses(state: _State) -> None:
    source = _export_source_snapshot(state)
    parsed = _export_parsed(state)
    profiles = _export_profiles(state)
    profile = profiles.get(state.data.get("code_profile_id"))
    if not isinstance(profile, Mapping):
        _block(
            "STRUCTURE_EXPORT_TARGET_PROFILE_MISSING",
            "/code_profile_id",
            "Loss analysis requires the registered export profile.",
        )
    preserves = profile.get("preserves_features")
    loss_code_map = profile.get("loss_codes")
    parsed_losses = parsed.get("lost_features")
    if (
        not isinstance(preserves, (list, tuple))
        or not isinstance(loss_code_map, Mapping)
        or not isinstance(parsed_losses, (list, tuple))
    ):
        _block(
            "STRUCTURE_EXPORT_LOSS_EVIDENCE_MISSING",
            "registry_snapshots/structure_export_profiles",
            "Loss analysis requires preserved-feature, loss-code, and parsed-loss evidence.",
        )
    lost_features = _source_features(source).difference(preserves)
    if set(parsed_losses) != lost_features:
        _fail(
            "STRUCTURE_EXPORT_LOSS_UNDISCLOSED",
            "/export_files/parsed/lost_features",
            "Parsed source-target capability loss differs from the registered profile reduction.",
        )
    try:
        required_codes = {loss_code_map[feature] for feature in lost_features}
    except KeyError:
        _block(
            "STRUCTURE_EXPORT_LOSS_CODE_REGISTRY_INCOMPLETE",
            "registry_snapshots/structure_export_profiles",
            "A lost feature lacks a stable registered loss code.",
        )
    roundtrip = state.data.get("roundtrip_validation")
    declared_codes = (
        set(roundtrip.get("loss_codes", ()))
        if isinstance(roundtrip, Mapping)
        else set()
    )
    classification = (
        roundtrip.get("classification") if isinstance(roundtrip, Mapping) else None
    )
    if declared_codes != required_codes:
        _fail(
            "STRUCTURE_EXPORT_LOSS_UNDISCLOSED",
            "/roundtrip_validation/loss_codes",
            "Declared loss codes do not exactly cover every target-format loss.",
        )
    if lost_features and classification == "exact":
        _fail(
            "STRUCTURE_EXPORT_LOSS_UNDISCLOSED",
            "/roundtrip_validation/classification",
            "Any target-format loss prevents an exact roundtrip classification.",
        )
    if not lost_features and classification == "lossy":
        _fail(
            "STRUCTURE_EXPORT_LOSS_UNDISCLOSED",
            "/roundtrip_validation/classification",
            "A lossy classification lacks a source-target capability loss.",
        )


def _trajectory_source_lineage(state: _State) -> None:
    for parts, ref in _iter_record_refs(state.data):
        state.resolve_ref(ref, _pointer(parts))
    source_ref = state.data.get("source_run_ref")
    segments = state.data.get("segments")
    if not isinstance(segments, (list, tuple)) or not segments:
        _block(
            "TRAJECTORY_SEGMENT_EVIDENCE_MISSING",
            "/segments",
            "Trajectory source ancestry requires segment declarations.",
        )
    for index, segment in enumerate(segments):
        if not isinstance(segment, Mapping):
            _block(
                "TRAJECTORY_SEGMENT_EVIDENCE_MISSING",
                f"/segments/{index}",
                "A segment declaration is malformed.",
            )
        segment_ref = segment.get("source_run_ref")
        if not _same_ref_identity(segment_ref, source_ref):
            segment_view = state.resolve_ref(
                segment_ref, f"/segments/{index}/source_run_ref"
            )
            ancestry = segment_view["data"].get("parent_refs")
            if not isinstance(ancestry, (list, tuple)) or not any(
                _same_ref_identity(item, source_ref) for item in ancestry
            ):
                _fail(
                    "TRAJECTORY_SOURCE_LINEAGE_HASH_MISMATCH",
                    f"/segments/{index}/source_run_ref",
                    "A segment run is neither the global source run nor its declared descendant.",
                )


def _trajectory_file_refs(state: _State) -> tuple[tuple[str, Mapping[str, Any]], ...]:
    refs: list[tuple[str, Mapping[str, Any]]] = []
    files = state.data.get("files")
    if not isinstance(files, (list, tuple)) or not files:
        _block(
            "TRAJECTORY_FILE_EVIDENCE_MISSING",
            "/files",
            "Trajectory files are missing.",
        )
    for index, ref in enumerate(files):
        if not isinstance(ref, Mapping):
            _block(
                "TRAJECTORY_FILE_EVIDENCE_MISSING",
                f"/files/{index}",
                "A trajectory file reference is malformed.",
            )
        refs.append((f"/files/{index}", ref))
    frame_index = state.data.get("frame_index")
    if not isinstance(frame_index, Mapping):
        _block(
            "TRAJECTORY_FILE_EVIDENCE_MISSING",
            "/frame_index",
            "Frame-index file reference is missing.",
        )
    refs.append(("/frame_index", frame_index))
    time_axis = state.data.get("time_axis")
    if isinstance(time_axis, Mapping) and time_axis.get("values_file") is not None:
        refs.append(("/time_axis/values_file", time_axis["values_file"]))
    for index, segment in enumerate(state.data.get("segments", ())):
        if isinstance(segment, Mapping) and segment.get("checkpoint_ref") is not None:
            refs.append(
                (f"/segments/{index}/checkpoint_ref", segment["checkpoint_ref"])
            )
    return tuple(refs)


def _trajectory_file_hashes(state: _State) -> None:
    for location, ref in _trajectory_file_refs(state):
        state.artifact_for_ref(ref, location)


def _trajectory_primary_parsed(state: _State) -> Mapping[str, Any]:
    candidates: list[Mapping[str, Any]] = []
    for index, ref in enumerate(state.data.get("files", ())):
        if not isinstance(ref, Mapping):
            continue
        view = state.artifact_for_ref(ref, f"/files/{index}", require_parsed=True)
        if ref.get("role") == "trajectory" and isinstance(view["data"], Mapping):
            candidates.append(view["data"])
    if len(candidates) != 1:
        _block(
            "TRAJECTORY_PARSED_DATA_AMBIGUOUS",
            "/files",
            "Exactly one authenticated trajectory-role artifact must provide parsed frame data.",
        )
    return candidates[0]


def _trajectory_frame_index_data(state: _State) -> Mapping[str, Any]:
    view = state.artifact_for_ref(
        state.data.get("frame_index"), "/frame_index", require_parsed=True
    )
    return view["data"]


def _trajectory_segment_ids(state: _State) -> None:
    segments = state.data.get("segments")
    if not isinstance(segments, (list, tuple)) or not segments:
        _block(
            "TRAJECTORY_SEGMENT_EVIDENCE_MISSING",
            "/segments",
            "Trajectory segments are missing.",
        )
    positions: dict[str, int] = {}
    parents: dict[str, str | None] = {}
    for index, segment in enumerate(segments):
        if not isinstance(segment, Mapping) or not isinstance(
            segment.get("segment_id"), str
        ):
            _block(
                "TRAJECTORY_SEGMENT_EVIDENCE_MISSING",
                f"/segments/{index}",
                "A segment lacks a stable segment_id.",
            )
        segment_id = segment["segment_id"]
        if segment_id in positions:
            _fail(
                "TRAJECTORY_SEGMENT_ID_NOT_UNIQUE",
                f"/segments/{index}/segment_id",
                "segment_id values must be unique.",
            )
        positions[segment_id] = index
        parents[segment_id] = segment.get("parent_segment_id")
    for segment_id, parent in parents.items():
        if parent is None:
            continue
        if parent not in positions:
            _fail(
                "TRAJECTORY_SEGMENT_PARENT_MISSING",
                f"/segments/{positions[segment_id]}/parent_segment_id",
                "parent_segment_id does not resolve.",
            )
        if positions[parent] >= positions[segment_id]:
            _fail(
                "TRAJECTORY_SEGMENT_PARENT_ORDER_INVALID",
                f"/segments/{positions[segment_id]}/parent_segment_id",
                "A segment parent must appear earlier in topological order.",
            )
    for start in parents:
        visiting: set[str] = set()
        node: str | None = start
        while node is not None:
            if node in visiting:
                _fail(
                    "TRAJECTORY_SEGMENT_PARENT_CYCLE",
                    "/segments",
                    "The segment-parent graph contains a cycle.",
                )
            visiting.add(node)
            node = parents.get(node)


def _trajectory_frame_indices(state: _State) -> None:
    parsed = _trajectory_frame_index_data(state)
    indices = parsed.get("frame_indices")
    locators = parsed.get("frame_locators")
    frame_count = state.data.get("frame_count")
    if (
        not isinstance(indices, (list, tuple))
        or not isinstance(locators, (list, tuple))
        or not isinstance(frame_count, int)
    ):
        _block(
            "TRAJECTORY_FRAME_INDEX_EVIDENCE_MISSING",
            "/frame_index",
            "Parsed frame indices, locators, or declared frame count are missing.",
        )
    if list(indices) != list(range(frame_count)) or len(indices) != len(set(indices)):
        _fail(
            "TRAJECTORY_FRAME_INDEX_NOT_UNIQUE",
            "/frame_index/parsed/frame_indices",
            "Parsed frame indices are not unique and contiguous.",
        )
    invalid_locator = any(
        not isinstance(locator, str) or not locator for locator in locators
    )
    if (
        len(locators) != frame_count
        or invalid_locator
        or len(set(locators)) != frame_count
    ):
        _fail(
            "TRAJECTORY_FRAME_INDEX_NOT_UNIQUE",
            "/frame_index/parsed/frame_locators",
            "Exactly one nonempty locator is required for every frame.",
        )


def _trajectory_frame_count(state: _State) -> None:
    primary = _trajectory_primary_parsed(state)
    index_data = _trajectory_frame_index_data(state)
    declared = state.data.get("frame_count")
    parsed_count = primary.get("frame_count")
    indices = index_data.get("frame_indices")
    if (
        not isinstance(declared, int)
        or not isinstance(parsed_count, int)
        or not isinstance(indices, (list, tuple))
    ):
        _block(
            "TRAJECTORY_FRAME_COUNT_EVIDENCE_MISSING",
            "/frame_count",
            "Declared, parsed, or indexed frame count is unavailable.",
        )
    union: set[int] = set()
    for index, segment in enumerate(state.data.get("segments", ())):
        if (
            not isinstance(segment, Mapping)
            or not isinstance(segment.get("first_frame"), int)
            or not isinstance(segment.get("last_frame"), int)
        ):
            _block(
                "TRAJECTORY_SEGMENT_EVIDENCE_MISSING",
                f"/segments/{index}",
                "Segment frame bounds are missing.",
            )
        union.update(range(segment["first_frame"], segment["last_frame"] + 1))
    if (
        parsed_count != declared
        or len(indices) != declared
        or union != set(range(declared))
    ):
        _fail(
            "TRAJECTORY_FRAME_COUNT_MISMATCH",
            "/frame_count",
            "Parsed, indexed, declared, and segment-union frame counts disagree.",
        )


def _trajectory_topology(state: _State) -> Mapping[str, Any]:
    topology = state.data.get("topology")
    if not isinstance(topology, Mapping):
        _block(
            "TRAJECTORY_TOPOLOGY_EVIDENCE_MISSING",
            "/topology",
            "Trajectory topology declaration is missing.",
        )
    if topology.get("status") == "unresolved":
        _block(
            "TRAJECTORY_TOPOLOGY_UNRESOLVED",
            "/topology/status",
            "Trajectory topology is unresolved.",
        )
    ref = (
        topology.get("ref")
        if topology.get("status") == "present"
        else state.data.get("initial_structure_ref")
    )
    _view, snapshot = _resolved_snapshot(state, ref, "/topology/ref")
    return snapshot


def _trajectory_atom_order(state: _State) -> None:
    topology = _trajectory_topology(state)
    topology_order = [
        site.get("site_id")
        for site in sorted(_sites(topology), key=lambda item: item.get("ordinal", -1))
    ]
    declared = state.data.get("site_order")
    atom_count = state.data.get("atom_count")
    frame_count = state.data.get("frame_count")
    if (
        not isinstance(declared, (list, tuple))
        or not isinstance(atom_count, int)
        or not isinstance(frame_count, int)
    ):
        _block(
            "TRAJECTORY_ATOM_ORDER_EVIDENCE_MISSING",
            "/site_order",
            "Declared atom count or site order is missing.",
        )
    if (
        len(declared) != atom_count
        or len(declared) != len(set(declared))
        or list(declared) != topology_order
    ):
        _fail(
            "TRAJECTORY_ATOM_COUNT_SITE_ORDER_MISMATCH",
            "/site_order",
            "Declared site order is not a unique complete topology order.",
        )
    parsed = _trajectory_primary_parsed(state)
    atom_counts = parsed.get("atom_counts")
    site_orders = parsed.get("site_orders")
    if (
        not isinstance(atom_counts, (list, tuple))
        or not isinstance(site_orders, (list, tuple))
        or len(atom_counts) != frame_count
        or len(site_orders) != frame_count
    ):
        _block(
            "TRAJECTORY_PER_FRAME_ATOM_EVIDENCE_MISSING",
            "/files/parsed",
            "Per-frame atom counts and site orders are required.",
        )
    if (
        any(value != atom_count for value in atom_counts)
        or any(
            list(value) != list(declared)
            for value in site_orders
            if isinstance(value, (list, tuple))
        )
        or any(not isinstance(value, (list, tuple)) for value in site_orders)
    ):
        _fail(
            "TRAJECTORY_ATOM_COUNT_SITE_ORDER_MISMATCH",
            "/files/parsed/site_orders",
            "At least one frame differs in atom count or site order.",
        )


def _segment_map(state: _State) -> tuple[dict[str, Mapping[str, Any]], dict[str, int]]:
    segments: dict[str, Mapping[str, Any]] = {}
    positions: dict[str, int] = {}
    for index, segment in enumerate(state.data.get("segments", ())):
        if not isinstance(segment, Mapping) or not isinstance(
            segment.get("segment_id"), str
        ):
            _block(
                "TRAJECTORY_SEGMENT_EVIDENCE_MISSING",
                f"/segments/{index}",
                "A segment declaration is malformed.",
            )
        segments[segment["segment_id"]] = segment
        positions[segment["segment_id"]] = index
    return segments, positions


def _trajectory_segment_ranges(state: _State) -> None:
    frame_count = state.data.get("frame_count")
    if not isinstance(frame_count, int):
        _block(
            "TRAJECTORY_SEGMENT_EVIDENCE_MISSING",
            "/frame_count",
            "Global frame count is missing.",
        )
    segments, positions = _segment_map(state)
    for segment_id, segment in segments.items():
        index = positions[segment_id]
        bounds = (
            segment.get("first_frame"),
            segment.get("last_frame"),
            segment.get("start_step"),
            segment.get("end_step"),
        )
        if not all(
            isinstance(value, int) and not isinstance(value, bool) for value in bounds
        ):
            _block(
                "TRAJECTORY_SEGMENT_EVIDENCE_MISSING",
                f"/segments/{index}",
                "Segment bounds must be integers.",
            )
        first, last, start_step, end_step = bounds
        if (
            first < 0
            or last < first
            or last >= frame_count
            or start_step < 0
            or end_step < start_step
        ):
            _fail(
                "TRAJECTORY_SEGMENT_RANGE_INVALID",
                f"/segments/{index}",
                "Segment frame or step bounds are outside ordered global limits.",
            )
        parent_id = segment.get("parent_segment_id")
        if parent_id is not None:
            parent = segments.get(parent_id)
            if parent is None or positions[parent_id] >= index:
                _fail(
                    "TRAJECTORY_SEGMENT_RANGE_INVALID",
                    f"/segments/{index}/parent_segment_id",
                    "Segment parent is missing or not earlier.",
                )
            label = segment.get("continuity_from_parent")
            if label == "continuous" and (
                first != parent["last_frame"] + 1
                or start_step != parent["end_step"] + 1
            ):
                _fail(
                    "TRAJECTORY_SEGMENT_RANGE_INVALID",
                    f"/segments/{index}",
                    "Continuous child ranges do not immediately follow the parent.",
                )
            if (
                label == "gapped"
                and first <= parent["last_frame"] + 1
                and start_step <= parent["end_step"] + 1
            ):
                _fail(
                    "TRAJECTORY_SEGMENT_RANGE_INVALID",
                    f"/segments/{index}",
                    "Gapped child ranges do not contain a gap.",
                )
            if (
                label == "overlapping"
                and first > parent["last_frame"]
                and start_step > parent["end_step"]
            ):
                _fail(
                    "TRAJECTORY_SEGMENT_RANGE_INVALID",
                    f"/segments/{index}",
                    "Overlapping child ranges do not overlap the parent.",
                )


def _trajectory_continuity(state: _State) -> None:
    segments, positions = _segment_map(state)
    parsed = _trajectory_primary_parsed(state)
    parsed_steps = parsed.get("steps")
    frame_count = state.data.get("frame_count")
    if (
        not isinstance(frame_count, int)
        or not isinstance(parsed_steps, (list, tuple))
        or len(parsed_steps) != frame_count
        or not all(
            isinstance(step, int) and not isinstance(step, bool)
            for step in parsed_steps
        )
    ):
        _block(
            "TRAJECTORY_CONTINUITY_EVIDENCE_MISSING",
            "/files/parsed/steps",
            "Parsed integer step values are required at every frame boundary.",
        )
    gaps = 0
    overlaps = 0
    for segment_id, segment in segments.items():
        first_frame = segment.get("first_frame")
        last_frame = segment.get("last_frame")
        if (
            not isinstance(first_frame, int)
            or not isinstance(last_frame, int)
            or first_frame < 0
            or last_frame >= frame_count
            or first_frame > last_frame
        ):
            _fail(
                "TRAJECTORY_CONTINUITY_MISMATCH",
                f"/segments/{positions[segment_id]}",
                "Segment frame bounds cannot index parsed trajectory boundaries.",
            )
        observed_start_step = parsed_steps[first_frame]
        observed_end_step = parsed_steps[last_frame]
        if (
            segment.get("start_step") != observed_start_step
            or segment.get("end_step") != observed_end_step
        ):
            _fail(
                "TRAJECTORY_CONTINUITY_MISMATCH",
                f"/segments/{positions[segment_id]}",
                "Declared segment step bounds differ from parsed frame steps.",
            )
        parent_id = segment.get("parent_segment_id")
        label = segment.get("continuity_from_parent")
        if parent_id is None:
            if label != "not-applicable":
                _fail(
                    "TRAJECTORY_CONTINUITY_MISMATCH",
                    f"/segments/{positions[segment_id]}/continuity_from_parent",
                    "A root segment must use not-applicable continuity.",
                )
            continue
        parent = segments.get(parent_id)
        if parent is None:
            _fail(
                "TRAJECTORY_CONTINUITY_MISMATCH",
                f"/segments/{positions[segment_id]}/parent_segment_id",
                "Continuity parent is missing.",
            )
        frame_delta = segment.get("first_frame") - parent.get("last_frame")
        parent_last_frame = parent.get("last_frame")
        if (
            not isinstance(parent_last_frame, int)
            or not 0 <= parent_last_frame < frame_count
        ):
            _fail(
                "TRAJECTORY_CONTINUITY_MISMATCH",
                f"/segments/{positions[parent_id]}/last_frame",
                "Parent frame boundary cannot index parsed trajectory steps.",
            )
        step_delta = observed_start_step - parsed_steps[parent_last_frame]
        if frame_delta == 1 and step_delta == 1:
            observed = "continuous"
        elif frame_delta > 1 or step_delta > 1:
            observed = "gapped"
            gaps += 1
        else:
            observed = "overlapping"
            overlaps += 1
        if label != observed:
            _fail(
                "TRAJECTORY_CONTINUITY_MISMATCH",
                f"/segments/{positions[segment_id]}/continuity_from_parent",
                "Parsed frame and step boundaries contradict the continuity label.",
            )
    continuity = state.data.get("continuity")
    if not isinstance(continuity, Mapping):
        _block(
            "TRAJECTORY_CONTINUITY_EVIDENCE_MISSING",
            "/continuity",
            "Global continuity declaration is missing.",
        )
    if gaps and overlaps:
        expected_status = "unresolved"
    elif gaps:
        expected_status = "gapped"
    elif overlaps:
        expected_status = "overlapping"
    else:
        expected_status = "continuous"
    if (
        continuity.get("status") != expected_status
        or continuity.get("gap_count") != gaps
        or continuity.get("overlap_count") != overlaps
    ):
        _fail(
            "TRAJECTORY_CONTINUITY_MISMATCH",
            "/continuity",
            "Global status and gap/overlap counts do not reduce from segment boundaries.",
        )
    for index, ref in enumerate(continuity.get("evidence_refs", ())):
        state.resolve_ref(ref, f"/continuity/evidence_refs/{index}")


def _trajectory_time_axis(state: _State) -> None:
    frame_count = state.data.get("frame_count")
    parsed = _trajectory_primary_parsed(state)
    times = parsed.get("times")
    axis = state.data.get("time_axis")
    if not isinstance(axis, Mapping) or not isinstance(frame_count, int):
        _block(
            "TRAJECTORY_TIME_EVIDENCE_MISSING",
            "/time_axis",
            "Time-axis declaration is missing.",
        )
    status = axis.get("status")
    if status in {"not-applicable", "unresolved"}:
        if status == "unresolved":
            _block(
                "TRAJECTORY_TIME_AXIS_UNRESOLVED",
                "/time_axis/status",
                "Time axis is explicitly unresolved.",
            )
        return
    if not isinstance(times, (list, tuple)) or len(times) != frame_count:
        _fail(
            "TRAJECTORY_TIME_AXIS_NONMONOTONIC",
            "/files/parsed/times",
            "Parsed time count differs from frame_count.",
        )
    numeric_times = [
        _finite_number(value, f"/files/parsed/times/{index}")
        for index, value in enumerate(times)
    ]
    if any(right <= left for left, right in zip(numeric_times, numeric_times[1:])):
        _fail(
            "TRAJECTORY_TIME_AXIS_NONMONOTONIC",
            "/files/parsed/times",
            "Time values are not strictly increasing.",
        )
    if status == "present-regular":
        start = _finite_number(axis.get("start"), "/time_axis/start")
        step = _finite_number(axis.get("step"), "/time_axis/step")
        if step <= 0:
            _fail(
                "TRAJECTORY_TIME_AXIS_NONMONOTONIC",
                "/time_axis/step",
                "Regular time step must be positive.",
            )
        tolerance = max(abs(step) * 1.0e-9, 1.0e-12)
        if any(
            abs(value - (start + index * step)) > tolerance
            for index, value in enumerate(numeric_times)
        ):
            _fail(
                "TRAJECTORY_TIME_AXIS_NONMONOTONIC",
                "/files/parsed/times",
                "Parsed times do not follow start + frame_index * step.",
            )
    elif status == "present-irregular":
        values_ref = axis.get("values_file")
        view = state.artifact_for_ref(
            values_ref, "/time_axis/values_file", require_parsed=True
        )
        declared_values = view["data"].get("values")
        if not isinstance(declared_values, (list, tuple)) or list(
            declared_values
        ) != list(times):
            _fail(
                "TRAJECTORY_TIME_AXIS_NONMONOTONIC",
                "/time_axis/values_file",
                "Irregular-time file values differ from parsed trajectory times.",
            )
    else:
        _block(
            "TRAJECTORY_TIME_EVIDENCE_MISSING",
            "/time_axis/status",
            "Unsupported time-axis status.",
        )


def _trajectory_pbc_cells(state: _State) -> None:
    parsed = _trajectory_primary_parsed(state)
    frame_count = state.data.get("frame_count")
    cells = parsed.get("cells")
    pbc = state.data.get("pbc")
    mode = state.data.get("cell_mode")
    if (
        not isinstance(frame_count, int)
        or not isinstance(cells, (list, tuple))
        or len(cells) != frame_count
    ):
        _block(
            "TRAJECTORY_CELL_EVIDENCE_MISSING",
            "/files/parsed/cells",
            "Parsed per-frame cells are missing.",
        )
    if (
        not isinstance(pbc, (list, tuple))
        or len(pbc) != 3
        or not all(isinstance(value, bool) for value in pbc)
    ):
        _block(
            "TRAJECTORY_CELL_EVIDENCE_MISSING",
            "/pbc",
            "PBC must be a three-boolean vector.",
        )
    if mode == "absent":
        if any(pbc) or any(cell is not None for cell in cells):
            _fail(
                "TRAJECTORY_PBC_CELL_MISMATCH",
                "/cell_mode",
                "Absent cells require nonperiodic PBC and null per-frame cells.",
            )
        return
    matrices = [
        _matrix3(cell, f"/files/parsed/cells/{index}")
        for index, cell in enumerate(cells)
    ]
    if any(abs(_determinant(matrix)) <= 1.0e-12 for matrix in matrices):
        _fail(
            "TRAJECTORY_PBC_CELL_MISMATCH",
            "/files/parsed/cells",
            "A parsed trajectory cell is singular.",
        )
    topology = _trajectory_topology(state)
    topology_periodicity = topology.get("periodicity")
    if not isinstance(topology_periodicity, Mapping) or list(
        topology_periodicity.get("pbc", ())
    ) != list(pbc):
        _fail(
            "TRAJECTORY_PBC_CELL_MISMATCH",
            "/pbc",
            "Trajectory PBC differs from the resolved topology declaration.",
        )
    tolerance = _snapshot_precision(topology)
    if mode == "fixed":
        reference = matrices[0]
        if any(
            max(_max_residual(a, b) for a, b in zip(reference, matrix, strict=True))
            > tolerance
            for matrix in matrices[1:]
        ):
            _fail(
                "TRAJECTORY_PBC_CELL_MISMATCH",
                "/files/parsed/cells",
                "Fixed-cell trajectory contains varying cells.",
            )
        if topology.get("cell", {}).get("status") == "present":
            topology_cell = _cell(topology)
            if (
                max(
                    _max_residual(a, b)
                    for a, b in zip(reference, topology_cell, strict=True)
                )
                > tolerance
            ):
                _fail(
                    "TRAJECTORY_PBC_CELL_MISMATCH",
                    "/files/parsed/cells/0",
                    "Fixed trajectory cell differs from topology cell.",
                )
    elif mode != "variable":
        _block(
            "TRAJECTORY_CELL_EVIDENCE_MISSING", "/cell_mode", "Unsupported cell mode."
        )


_HANDLERS: dict[str, Callable[[_State], None]] = {
    "structure-site-identity-not-unique": _snapshot_identity_not_unique,
    "structure-composition-site-mismatch": _snapshot_composition,
    "structure-periodicity-cell-mismatch": _snapshot_periodicity,
    "structure-coordinate-representation-mismatch": _snapshot_coordinates,
    "structure-charge-spin-electron-parity-mismatch": _snapshot_charge_spin,
    "structure-identity-fingerprint-mismatch": _snapshot_identity,
    "molecular-snapshot-hash-mismatch": _molecular_snapshot_hash,
    "molecular-site-reference-missing": _molecular_site_references,
    "molecular-charge-multiplicity-electron-parity-mismatch": _molecular_quantum_parity,
    "molecular-connectivity-inconsistent": _molecular_connectivity,
    "molecular-fragment-coverage-inconsistent": _molecular_fragment_coverage,
    "molecular-extraction-lineage-mismatch": _molecular_extraction_lineage,
    "structure-transform-reference-hash-mismatch": _transformation_reference_hashes,
    "structure-transform-mapping-id-not-unique": _transformation_mapping_ids,
    "structure-transform-site-reference-missing": _transformation_site_references,
    "structure-transform-mapping-coverage-incomplete": _transformation_mapping_coverage,
    "structure-transform-relation-cardinality-mismatch": _transformation_relation_cardinality,
    "structure-transform-image-shift-inconsistent": _transformation_image_shifts,
    "structure-transform-operation-semantics-mismatch": _transformation_operation_semantics,
    "structure-transform-roundtrip-fingerprint-mismatch": _transformation_roundtrip,
    "structure-transform-tolerance-unverified": _transformation_tolerance,
    "structure-export-source-hash-mismatch": _export_source_hashes,
    "structure-export-file-hash-mismatch": _export_file_hashes,
    "structure-export-output-index-not-unique": _export_output_indices,
    "structure-export-atom-map-incomplete": _export_atom_map,
    "structure-export-unit-map-inconsistent": _export_unit_mapping,
    "structure-export-target-profile-mismatch": _export_target_profile,
    "structure-export-roundtrip-fingerprint-mismatch": _export_roundtrip,
    "structure-export-loss-undisclosed": _export_losses,
    "trajectory-source-lineage-hash-mismatch": _trajectory_source_lineage,
    "trajectory-file-hash-mismatch": _trajectory_file_hashes,
    "trajectory-segment-id-not-unique": _trajectory_segment_ids,
    "trajectory-frame-index-not-unique": _trajectory_frame_indices,
    "trajectory-frame-count-mismatch": _trajectory_frame_count,
    "trajectory-atom-count-site-order-mismatch": _trajectory_atom_order,
    "trajectory-segment-range-invalid": _trajectory_segment_ranges,
    "trajectory-continuity-mismatch": _trajectory_continuity,
    "trajectory-time-axis-nonmonotonic": _trajectory_time_axis,
    "trajectory-pbc-cell-mismatch": _trajectory_pbc_cells,
    "record-reference-dag-invalid": _check_all_record_refs,
}
if frozenset(_HANDLERS) != OBLIGATION_IDS:
    raise RuntimeError(
        "structure semantic handler table is out of sync with obligations"
    )


def _expected_contracts(obligation_id: str) -> frozenset[str]:
    if obligation_id == "record-reference-dag-invalid":
        return frozenset(CONTRACT_NAMES)
    if obligation_id in SNAPSHOT_OBLIGATIONS:
        return frozenset({"structure-snapshot"})
    if obligation_id in MOLECULAR_OBLIGATIONS:
        return frozenset({"molecular-structure-manifest"})
    if obligation_id in TRANSFORMATION_OBLIGATIONS:
        return frozenset({"structure-transformation-manifest"})
    if obligation_id in EXPORT_OBLIGATIONS:
        return frozenset({"structure-export-manifest"})
    if obligation_id in TRAJECTORY_OBLIGATIONS:
        return frozenset({"atomistic-trajectory-manifest"})
    return frozenset()


def _handler_id(obligation_id: str) -> str:
    return f"bundle-semantics-structure.{obligation_id}"


def _result(
    obligation_id: str,
    status: str,
    finding_codes: Sequence[str],
    location: str,
    message: str,
    handler_id: str | None,
) -> dict[str, Any]:
    return {
        "obligation_id": obligation_id,
        "status": status,
        "finding_codes": sorted(set(finding_codes)),
        "location": location,
        "message": message,
        "handler_id": handler_id,
    }


def evaluate(
    obligation_ids: Sequence[str], context: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Evaluate each distinct advertised structure obligation exactly once.

    Evidence-backed assertion violations return ``fail``.  Missing, inactive,
    unknown, malformed, or unavailable evidence returns ``blocked``.  No
    exception or absent handler can become a passing result.
    """

    if isinstance(obligation_ids, str):
        advertised: Sequence[Any] = (obligation_ids,)
    else:
        try:
            advertised = tuple(obligation_ids)
        except TypeError:
            advertised = ()
    normalized: list[str] = []
    invalid = False
    for item in advertised:
        if not isinstance(item, str) or not item:
            invalid = True
            continue
        if item not in normalized:
            normalized.append(item)
    if invalid and not normalized:
        normalized.append("UNPARSEABLE_STRUCTURE_OBLIGATION")

    try:
        state = _State(context)
    except _Problem as problem:
        state = None
        context_problem = problem
    except Exception:
        state = None
        context_problem = _problem(
            "blocked",
            "STRUCTURE_SEMANTIC_CONTEXT_INVALID",
            "semantic-context",
            "The structure evaluator could not validate the frozen context.",
        )
    else:
        context_problem = None

    results: list[dict[str, Any]] = []
    for obligation_id in normalized:
        handler = _HANDLERS.get(obligation_id)
        handler_id = _handler_id(obligation_id) if handler is not None else None
        if handler is None:
            results.append(
                _result(
                    obligation_id,
                    "blocked",
                    ["SEMANTIC_OBLIGATION_HANDLER_MISSING"],
                    "semantic-obligation",
                    "No trusted structure handler implements this advertised obligation.",
                    None,
                )
            )
            continue
        if context_problem is not None or state is None:
            problem = context_problem or _problem(
                "blocked",
                "STRUCTURE_SEMANTIC_CONTEXT_INVALID",
                "semantic-context",
                "The structure semantic context is unavailable.",
            )
            results.append(
                _result(
                    obligation_id,
                    problem.status,
                    problem.finding_codes,
                    problem.location,
                    problem.message,
                    handler_id,
                )
            )
            continue
        try:
            state.require_current_integrity()
            contract_name = state.data.get("contract_name")
            if contract_name not in _expected_contracts(obligation_id):
                _block(
                    "STRUCTURE_OBLIGATION_CONTRACT_MISMATCH",
                    "/contract_name",
                    "This obligation is not advertised by the current structure contract.",
                )
            handler(state)
        except _Problem as problem:
            results.append(
                _result(
                    obligation_id,
                    problem.status,
                    problem.finding_codes,
                    problem.location,
                    problem.message,
                    handler_id,
                )
            )
        except Exception:
            results.append(
                _result(
                    obligation_id,
                    "blocked",
                    ["STRUCTURE_SEMANTIC_EVALUATOR_INTERNAL_ERROR"],
                    "semantic-obligation",
                    "The trusted structure handler could not complete deterministically.",
                    handler_id,
                )
            )
        else:
            results.append(
                _result(
                    obligation_id,
                    "pass",
                    [],
                    f"record:{state.current_identity[0]}:{state.current_identity[2]}",
                    "The structure semantic assertion was established from authenticated parsed evidence.",
                    handler_id,
                )
            )
    return results
