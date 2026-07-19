#!/usr/bin/env python3
"""Production semantic-obligation dispatcher for validated bundle objects.

Domain evaluators receive only already-parsed, read-only views.  They must not
read files, resolve paths, import a module named by bundle data, or reinterpret
raw untrusted input.  This dispatcher accounts for every advertised obligation
exactly once and converts any evaluator defect into a blocked result.

``records_by_identity`` is keyed by
``(contract_name, schema_version, record_id)``.  Its values, and
``current_record``, have exactly these fields::

    {contract_name, schema_version, record_id, index, data, raw_sha256,
     lifecycle, integrity_verified_active}

``artifacts_by_label`` values have exactly these fields::

    {label, index, metadata, raw_sha256, bytes, integrity_verified,
     parser_observations}
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import importlib
import re
from types import MappingProxyType
from typing import Any


STATUSES = frozenset({"pass", "fail", "blocked"})
REQUIRED_RESULT_FIELDS = frozenset(
    {
        "obligation_id",
        "status",
        "finding_codes",
        "location",
        "message",
        "handler_id",
    }
)
# Only these repository-owned module names can ever be imported.  Bundle or CLI
# data cannot select Python code.  New domains require an explicit reviewed code
# change to this allowlist.
BUILTIN_DOMAIN_MODULES = (
    "bundle_semantics_legacy",
    "bundle_semantics_structure",
    "bundle_semantics_execution",
    "bundle_semantics_evidence",
)
# Record-contract obligations are domain-owned in Wave 0.  Generic bundle-core
# facts remain available through ``context['core_checks']`` for those trusted
# handlers to consume, but the dispatcher must never infer ownership from an
# obligation substring.  A future core-owned obligation requires an explicit,
# reviewed exact-ID entry here.
CORE_OBLIGATION_HANDLERS: Mapping[str, str] = MappingProxyType(
    {
        # The five legacy schemas deliberately delegate only their repository-
        # wide privacy assertion to the bundle core.  All hash, lineage,
        # readiness, and claim-ceiling assertions remain domain-owned.
        "LEGACY_ARTIFACT_PRIVACY_SAFE": "privacy-boundary",
        "LEGACY_DATASET_PRIVACY_SAFE": "privacy-boundary",
        "LEGACY_PLAN_PRIVACY_SAFE": "privacy-boundary",
        "LEGACY_TOOL_EXECUTION_PRIVACY_SAFE": "privacy-boundary",
        "LEGACY_STRUCTURE_PRIVACY_SAFE": "privacy-boundary",
    }
)

_FINDING_CODE = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")

DomainEvaluator = Callable[
    [Sequence[str], Mapping[str, Any]],
    Sequence[Mapping[str, Any]],
]


def freeze(value: Any) -> Any:
    """Recursively expose ordinary JSON-shaped data through read-only views."""

    if isinstance(value, Mapping):
        return MappingProxyType({key: freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(item) for item in value)
    return value


def read_only_context(value: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate and freeze the stable domain-evaluator context interface."""

    required = {
        "current_record",
        "current_record_index",
        "records_by_identity",
        "artifacts_by_label",
        "core_checks",
        "registry_snapshots",
    }
    if set(value) != required:
        missing = sorted(required.difference(value))
        extra = sorted(set(value).difference(required))
        raise ValueError(f"semantic context fields mismatch; missing={missing}, extra={extra}")
    if not isinstance(value["current_record_index"], int):
        raise ValueError("semantic context current_record_index must be an integer")
    for field in (
        "current_record",
        "records_by_identity",
        "artifacts_by_label",
        "core_checks",
        "registry_snapshots",
    ):
        if not isinstance(value[field], Mapping):
            raise ValueError(f"semantic context {field} must be a mapping")
    record_fields = {
        "contract_name",
        "schema_version",
        "record_id",
        "index",
        "data",
        "raw_sha256",
        "lifecycle",
        "integrity_verified_active",
    }
    artifact_fields = {
        "label",
        "index",
        "metadata",
        "raw_sha256",
        "bytes",
        "integrity_verified",
        "parser_observations",
    }
    current = value["current_record"]
    if set(current) != record_fields:
        raise ValueError("semantic current_record view has an invalid shape")
    for identity, record in value["records_by_identity"].items():
        if not (
            isinstance(identity, tuple)
            and len(identity) == 3
            and all(isinstance(item, str) for item in identity)
            and isinstance(record, Mapping)
            and set(record) == record_fields
        ):
            raise ValueError("semantic records_by_identity entry has an invalid shape")
        if identity != (
            record["contract_name"],
            record["schema_version"],
            record["record_id"],
        ):
            raise ValueError("semantic record identity key does not match its view")
    current_identity = (
        current["contract_name"],
        current["schema_version"],
        current["record_id"],
    )
    if value["records_by_identity"].get(current_identity) != current:
        raise ValueError("semantic current_record differs from its indexed record view")
    for label, artifact in value["artifacts_by_label"].items():
        if not (
            isinstance(label, str)
            and isinstance(artifact, Mapping)
            and set(artifact) == artifact_fields
            and artifact.get("label") == label
        ):
            raise ValueError("semantic artifacts_by_label entry has an invalid shape")
        metadata = artifact["metadata"]
        observations = artifact["parser_observations"]
        if not isinstance(metadata, Mapping) or "path" in metadata:
            raise ValueError("semantic artifact metadata must be a path-free mapping")
        if not isinstance(artifact["index"], int) or artifact["index"] < 0:
            raise ValueError("semantic artifact index must be a nonnegative integer")
        if not isinstance(artifact["integrity_verified"], bool):
            raise ValueError("semantic artifact integrity flag must be boolean")
        if artifact["raw_sha256"] is not None and (
            not isinstance(artifact["raw_sha256"], str)
            or _SHA256.fullmatch(artifact["raw_sha256"]) is None
        ):
            raise ValueError("semantic artifact raw_sha256 must be null or lowercase sha256")
        if artifact["bytes"] is not None and (
            not isinstance(artifact["bytes"], int)
            or isinstance(artifact["bytes"], bool)
            or artifact["bytes"] < 0
        ):
            raise ValueError("semantic artifact bytes must be null or nonnegative integer")
        if not isinstance(observations, (list, tuple)):
            raise ValueError("semantic parser_observations must be a sequence")
        observation_fields = {
            "parser_id",
            "parser_version",
            "parser_component_sha256",
            "source_raw_sha256",
            "status",
            "observations",
        }
        for observation in observations:
            if not isinstance(observation, Mapping) or set(observation) != observation_fields:
                raise ValueError("semantic parser observation has an invalid shape")
            if (
                not isinstance(observation["parser_id"], str)
                or not observation["parser_id"]
                or not isinstance(observation["parser_version"], str)
                or not observation["parser_version"]
                or not isinstance(observation["parser_component_sha256"], str)
                or _SHA256.fullmatch(observation["parser_component_sha256"]) is None
                or not isinstance(observation["source_raw_sha256"], str)
                or _SHA256.fullmatch(observation["source_raw_sha256"]) is None
                or observation["source_raw_sha256"] != artifact["raw_sha256"]
                or observation["status"] not in STATUSES
                or not isinstance(observation["observations"], Mapping)
            ):
                raise ValueError("semantic parser observation identity or payload is invalid")
    return freeze(value)


def builtin_evaluator(contract_name: str) -> DomainEvaluator | None:
    """Resolve exactly one owner from the fixed repository allowlist.

    Allowlist order is never precedence: zero owners, multiple owners, a broken
    module, or a malformed ownership declaration all fail closed as ``None``.
    """

    matches: list[DomainEvaluator] = []
    for module_name in BUILTIN_DOMAIN_MODULES:
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            return None
        except Exception:
            return None
        contract_names = getattr(module, "CONTRACT_NAMES", ())
        evaluator = getattr(module, "evaluate", None)
        if (
            not isinstance(contract_names, (list, tuple, set, frozenset))
            or any(not isinstance(name, str) or not name for name in contract_names)
            or len(contract_names) != len(set(contract_names))
            or not callable(evaluator)
        ):
            return None
        if contract_name in contract_names:
            matches.append(evaluator)
    return matches[0] if len(matches) == 1 else None


def builtin_ownership_errors() -> list[str]:
    """Audit exact-one contract ownership without accepting import order.

    This is intentionally a small production API so repository tests can prove
    that a newly added domain module cannot shadow an existing evaluator.
    """

    owners: dict[str, list[str]] = {}
    errors: list[str] = []
    for module_name in BUILTIN_DOMAIN_MODULES:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            errors.append(f"{module_name}: import failed ({type(exc).__name__})")
            continue
        contract_names = getattr(module, "CONTRACT_NAMES", None)
        evaluator = getattr(module, "evaluate", None)
        if not isinstance(contract_names, (list, tuple, set, frozenset)):
            errors.append(f"{module_name}: CONTRACT_NAMES is missing or malformed")
            continue
        names = list(contract_names)
        if any(not isinstance(name, str) or not name for name in names):
            errors.append(f"{module_name}: CONTRACT_NAMES contains an invalid name")
            continue
        if len(names) != len(set(names)):
            errors.append(f"{module_name}: CONTRACT_NAMES contains duplicates")
        if not callable(evaluator):
            errors.append(f"{module_name}: evaluate is unavailable")
            continue
        for name in set(names):
            owners.setdefault(name, []).append(module_name)
    for name, modules in sorted(owners.items()):
        if len(modules) != 1:
            errors.append(f"{name}: expected exactly one owner, found {sorted(modules)}")
    return errors


def _core_handler(obligation_id: str) -> str | None:
    return CORE_OBLIGATION_HANDLERS.get(obligation_id)


def _blocked(
    obligation_id: str,
    code: str,
    *,
    message: str,
    location: str = "semantic-obligation",
) -> dict[str, Any]:
    return {
        "obligation_id": obligation_id,
        "status": "blocked",
        "finding_codes": [code],
        "location": location,
        "message": message,
        "handler_id": None,
    }


def _validated_result(
    obligation_id: str, candidate: object
) -> dict[str, Any] | None:
    if not isinstance(candidate, Mapping) or set(candidate) != REQUIRED_RESULT_FIELDS:
        return None
    if candidate.get("obligation_id") != obligation_id:
        return None
    if candidate.get("status") not in STATUSES:
        return None
    codes = candidate.get("finding_codes")
    if not isinstance(codes, (list, tuple)) or not all(
        isinstance(code, str) and _FINDING_CODE.fullmatch(code) is not None
        for code in codes
    ):
        return None
    if len(codes) != len(set(codes)):
        return None
    if (candidate.get("status") == "pass" and codes) or (
        candidate.get("status") in {"fail", "blocked"} and not codes
    ):
        return None
    if not isinstance(candidate.get("location"), str) or not candidate["location"]:
        return None
    if not isinstance(candidate.get("message"), str) or not candidate["message"]:
        return None
    handler_id = candidate.get("handler_id")
    if handler_id is not None and (not isinstance(handler_id, str) or not handler_id):
        return None
    return {
        "obligation_id": obligation_id,
        "status": candidate["status"],
        "finding_codes": sorted(codes),
        "location": candidate["location"],
        "message": candidate["message"],
        "handler_id": handler_id,
    }


def evaluate_advertised_obligations(
    obligation_ids: Sequence[object],
    context: Mapping[str, Any],
    *,
    evaluator: DomainEvaluator | None = None,
) -> list[dict[str, Any]]:
    """Account exactly once for every distinct advertised obligation.

    Core record-reference, DAG, artifact-integrity, and privacy obligations use
    precomputed checks in ``context``.  Remaining obligations are delegated to a
    repository-owned evaluator.  Missing, duplicate, extra, malformed, or
    exceptional domain results are always converted to ``blocked``.
    """

    frozen = read_only_context(context)
    normalized: list[str] = []
    invalid_positions = False
    for item in obligation_ids:
        if not isinstance(item, str) or not item:
            invalid_positions = True
            continue
        if item not in normalized:
            normalized.append(item)
    if invalid_positions:
        blocked = [
            _blocked(
                obligation_id,
                "INVALID_ADVERTISED_OBLIGATION",
                message="The schema obligation set contains a non-string or empty ID.",
            )
            for obligation_id in normalized
        ]
        blocked.append(
            _blocked(
                "UNPARSEABLE_ADVERTISED_OBLIGATION",
                "INVALID_ADVERTISED_OBLIGATION",
                message="At least one advertised obligation has no valid string identity.",
            )
        )
        return blocked
    duplicates = {
        item for item in normalized if sum(candidate == item for candidate in obligation_ids) > 1
    }
    results: dict[str, dict[str, Any]] = {}
    delegated: list[str] = []
    core_checks = frozen["core_checks"]
    for obligation_id in normalized:
        if obligation_id in duplicates:
            results[obligation_id] = _blocked(
                obligation_id,
                "DUPLICATE_ADVERTISED_OBLIGATION",
                message="The schema advertises this obligation more than once.",
            )
            continue
        handler_id = _core_handler(obligation_id)
        if handler_id is None:
            delegated.append(obligation_id)
            continue
        check = core_checks.get(handler_id)
        if not isinstance(check, Mapping):
            results[obligation_id] = _blocked(
                obligation_id,
                "CORE_OBLIGATION_CHECK_MISSING",
                message="The bundle core did not supply the required precomputed check.",
            )
            continue
        candidate = {
            "obligation_id": obligation_id,
            "status": check.get("status"),
            "finding_codes": list(check.get("finding_codes", ())),
            "location": f"core:{handler_id}",
            "message": "Evaluated from strict bundle-core integrity results.",
            "handler_id": handler_id,
        }
        validated = _validated_result(obligation_id, candidate)
        results[obligation_id] = validated or _blocked(
            obligation_id,
            "CORE_OBLIGATION_CHECK_INVALID",
            message="The bundle core supplied a malformed precomputed check.",
        )

    if delegated:
        if evaluator is None:
            for obligation_id in delegated:
                results[obligation_id] = _blocked(
                    obligation_id,
                    "OBLIGATION_HANDLER_UNAVAILABLE",
                    message="No trusted production domain evaluator handles this obligation.",
                )
        else:
            try:
                raw_domain_results = evaluator(tuple(delegated), frozen)
                domain_results = list(raw_domain_results)
            except Exception:
                domain_results = []
                evaluator_failed = True
            else:
                evaluator_failed = False
            by_id: dict[str, list[object]] = {}
            unknown_output = False
            for candidate in domain_results:
                if not isinstance(candidate, Mapping):
                    unknown_output = True
                    continue
                output_id = candidate.get("obligation_id")
                if output_id not in delegated:
                    unknown_output = True
                    continue
                by_id.setdefault(output_id, []).append(candidate)
            for obligation_id in delegated:
                candidates = by_id.get(obligation_id, [])
                if evaluator_failed:
                    results[obligation_id] = _blocked(
                        obligation_id,
                        "DOMAIN_EVALUATOR_FAILED",
                        message="The production domain evaluator raised an exception.",
                    )
                elif unknown_output:
                    results[obligation_id] = _blocked(
                        obligation_id,
                        "DOMAIN_EVALUATOR_UNKNOWN_OUTPUT",
                        message="The domain evaluator returned an unadvertised or malformed result.",
                    )
                elif len(candidates) == 0:
                    results[obligation_id] = _blocked(
                        obligation_id,
                        "DOMAIN_EVALUATOR_RESULT_MISSING",
                        message="The domain evaluator omitted this advertised obligation.",
                    )
                elif len(candidates) > 1:
                    results[obligation_id] = _blocked(
                        obligation_id,
                        "DOMAIN_EVALUATOR_RESULT_DUPLICATE",
                        message="The domain evaluator returned this obligation more than once.",
                    )
                else:
                    validated = _validated_result(obligation_id, candidates[0])
                    results[obligation_id] = validated or _blocked(
                        obligation_id,
                        "DOMAIN_EVALUATOR_RESULT_INVALID",
                        message="The domain evaluator returned a malformed result.",
                    )

    return [results[obligation_id] for obligation_id in normalized]
