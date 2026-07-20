#!/usr/bin/env python3
"""Audit Schema semantic-obligation declarations and fail-closed ownership."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any, Sequence

import bundle_semantics
from registry_yaml import RegistryYAMLError, load_yaml_strict
import validate_contract


VALIDATOR_ID = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
OBLIGATION_ID = re.compile(
    r"^(?:[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*|[a-z][a-z0-9]*(?:-[a-z0-9]+)*)$"
)
IMPLEMENTATION_STATES = frozenset({"implemented", "blocked"})
CLAIM_CEILINGS = frozenset(
    {
        "no_positive_claim",
        "documented_behavior_only",
        "input_gates_only",
        "technical_run_gates_only",
        "numerical_candidate_only",
        "eligible_for_expert_review",
    }
)
STRUCTURED_OBLIGATION_FIELDS = frozenset(
    {
        "finding_id",
        "scope",
        "enforcement",
        "blocks",
        "assertion",
        "evidence_required",
    }
)


@dataclass(frozen=True, order=True)
class Finding:
    code: str
    location: str
    message: str

    def render(self) -> str:
        return f"{self.code}\t{self.location}\t{self.message}"


@dataclass(frozen=True)
class Declaration:
    contract_name: str
    schema_version: str
    validator_id: str
    obligation_ids: tuple[str, ...]
    form: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _safe_relative_path(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path.as_posix()


def _unique_nonempty_strings(value: object) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and bool(item.strip()) for item in value)
        and len(value) == len(set(value))
    )


def _parse_obligation(
    value: object,
    location: str,
) -> tuple[str | None, list[Finding]]:
    if isinstance(value, str):
        if OBLIGATION_ID.fullmatch(value) is None:
            return None, [
                Finding(
                    "SEMANTIC_OBLIGATION_ID_INVALID",
                    location,
                    f"invalid obligation ID {value!r}",
                )
            ]
        return value, []
    if not isinstance(value, dict):
        return None, [
            Finding(
                "SEMANTIC_OBLIGATION_INVALID",
                location,
                "obligation must be an ID string or a structured object",
            )
        ]

    findings: list[Finding] = []
    missing = sorted(STRUCTURED_OBLIGATION_FIELDS.difference(value))
    extra = sorted(set(value).difference(STRUCTURED_OBLIGATION_FIELDS))
    if missing:
        findings.append(
            Finding(
                "SEMANTIC_STRUCTURED_OBLIGATION_FIELDS_MISSING",
                location,
                f"missing fields: {missing}",
            )
        )
    if extra:
        findings.append(
            Finding(
                "SEMANTIC_STRUCTURED_OBLIGATION_EXTRA_FIELDS",
                location,
                f"unexpected fields: {extra}",
            )
        )
    finding_id = value.get("finding_id")
    if not isinstance(finding_id, str) or OBLIGATION_ID.fullmatch(finding_id) is None:
        findings.append(
            Finding(
                "SEMANTIC_OBLIGATION_ID_INVALID",
                f"{location}/finding_id",
                f"invalid obligation ID {finding_id!r}",
            )
        )
    for field in ("scope", "enforcement", "assertion"):
        candidate = value.get(field)
        if not isinstance(candidate, str) or not candidate.strip():
            findings.append(
                Finding(
                    "SEMANTIC_STRUCTURED_OBLIGATION_FIELD_INVALID",
                    f"{location}/{field}",
                    "field must be a nonempty string",
                )
            )
    if value.get("enforcement") != "external-semantic-validator-required":
        findings.append(
            Finding(
                "SEMANTIC_STRUCTURED_OBLIGATION_ENFORCEMENT_INVALID",
                f"{location}/enforcement",
                "structured obligations must fail closed through the external semantic validator",
            )
        )
    for field in ("blocks", "evidence_required"):
        if not _unique_nonempty_strings(value.get(field)):
            findings.append(
                Finding(
                    "SEMANTIC_STRUCTURED_OBLIGATION_LIST_INVALID",
                    f"{location}/{field}",
                    "field must be a nonempty unique string list",
                )
            )
    if findings or not isinstance(finding_id, str):
        return None, findings
    return finding_id, []


def parse_declaration(
    contract: validate_contract.ContractSchema,
) -> tuple[Declaration | None, list[Finding]]:
    raw = contract.schema.get("x-vibe-semantic-obligations")
    location = f"contracts/{contract.filename}/x-vibe-semantic-obligations"
    if raw is None:
        return None, []
    findings: list[Finding] = []
    if isinstance(raw, list):
        validator_id: object = "bundle-semantic-dispatcher"
        obligations: object = raw
        form = "list"
    elif isinstance(raw, dict):
        validator_id = raw.get("validator")
        obligations = raw.get("required_checks")
        form = "object"
        extra = sorted(set(raw).difference({"validator", "required_checks"}))
        if extra:
            findings.append(
                Finding(
                    "SEMANTIC_DECLARATION_EXTRA_FIELDS",
                    location,
                    f"unexpected fields: {extra}",
                )
            )
    else:
        return None, [
            Finding(
                "SEMANTIC_DECLARATION_INVALID",
                location,
                "declaration must be a list or an object",
            )
        ]

    if not isinstance(validator_id, str) or VALIDATOR_ID.fullmatch(validator_id) is None:
        findings.append(
            Finding(
                "SEMANTIC_VALIDATOR_ID_INVALID",
                location,
                f"invalid validator ID {validator_id!r}",
            )
        )
    if not isinstance(obligations, list) or not obligations:
        findings.append(
            Finding(
                "SEMANTIC_OBLIGATION_LIST_INVALID",
                location,
                "required obligations must be a nonempty list",
            )
        )
        return None, findings

    normalized: list[str] = []
    for index, obligation in enumerate(obligations):
        obligation_id, obligation_findings = _parse_obligation(
            obligation,
            f"{location}/{index}",
        )
        findings.extend(obligation_findings)
        if obligation_id is not None:
            normalized.append(obligation_id)
    if len(normalized) != len(set(normalized)):
        findings.append(
            Finding(
                "SEMANTIC_OBLIGATION_DUPLICATE",
                location,
                "obligation IDs must be unique within a contract",
            )
        )
    if findings or not isinstance(validator_id, str):
        return None, findings
    return (
        Declaration(
            contract_name=contract.name,
            schema_version=contract.version,
            validator_id=validator_id,
            obligation_ids=tuple(normalized),
            form=form,
        ),
        [],
    )


def _load_registry(root: Path) -> tuple[dict[str, Any] | None, list[Finding]]:
    path = root / "registry" / "semantic-obligations.yaml"
    try:
        value = load_yaml_strict(path)
    except (OSError, UnicodeError, RegistryYAMLError) as exc:
        return None, [Finding("SEMANTIC_REGISTRY_UNREADABLE", str(path), str(exc))]
    if not isinstance(value, dict) or value.get("schema_version") != "1.0":
        return None, [
            Finding(
                "SEMANTIC_REGISTRY_SCHEMA_INVALID",
                "registry/semantic-obligations.yaml",
                "schema_version must be 1.0",
            )
        ]
    return value, []


def _validate_registry(
    root: Path,
    registry: dict[str, Any],
) -> tuple[dict[str, str], list[Finding]]:
    findings: list[Finding] = []
    validators = registry.get("validators")
    if not isinstance(validators, dict) or not validators:
        return {}, [
            Finding(
                "SEMANTIC_REGISTRY_VALIDATORS_INVALID",
                "registry/semantic-obligations.yaml/validators",
                "validators must be a nonempty mapping",
            )
        ]
    if not isinstance(registry.get("policies"), dict):
        findings.append(
            Finding(
                "SEMANTIC_REGISTRY_POLICIES_INVALID",
                "registry/semantic-obligations.yaml/policies",
                "policies must be a mapping",
            )
        )

    states: dict[str, str] = {}
    for validator_id, specification in sorted(validators.items()):
        location = f"registry/semantic-obligations.yaml/validators/{validator_id}"
        if not isinstance(validator_id, str) or VALIDATOR_ID.fullmatch(validator_id) is None:
            findings.append(
                Finding("SEMANTIC_REGISTRY_VALIDATOR_ID_INVALID", location, "invalid validator ID")
            )
            continue
        if not isinstance(specification, dict):
            findings.append(
                Finding("SEMANTIC_REGISTRY_VALIDATOR_INVALID", location, "validator must be a mapping")
            )
            continue
        state = specification.get("implementation")
        if state not in IMPLEMENTATION_STATES:
            findings.append(
                Finding(
                    "SEMANTIC_REGISTRY_IMPLEMENTATION_INVALID",
                    location,
                    f"implementation must be one of {sorted(IMPLEMENTATION_STATES)}",
                )
            )
            continue
        states[validator_id] = str(state)
        if specification.get("maximum_claim_when_unavailable") not in CLAIM_CEILINGS:
            findings.append(
                Finding(
                    "SEMANTIC_REGISTRY_CLAIM_CEILING_INVALID",
                    location,
                    "invalid unavailable claim ceiling",
                )
            )
        entrypoint = specification.get("entrypoint")
        dispatcher = specification.get("dispatcher")
        if state == "implemented":
            for field, candidate in (("entrypoint", entrypoint), ("dispatcher", dispatcher)):
                relative = _safe_relative_path(candidate)
                if relative is None or not root.joinpath(*PurePosixPath(relative).parts).is_file():
                    findings.append(
                        Finding(
                            "SEMANTIC_REGISTRY_IMPLEMENTED_PATH_MISSING",
                            f"{location}/{field}",
                            "implemented validator path is missing or unsafe",
                        )
                    )
        else:
            if entrypoint is not None or dispatcher is not None:
                findings.append(
                    Finding(
                        "SEMANTIC_REGISTRY_BLOCKED_PATH_PRESENT",
                        location,
                        "blocked validator must not advertise executable paths",
                    )
                )
            blocker = specification.get("blocker")
            if not isinstance(blocker, str) or len(blocker.strip()) < 20:
                findings.append(
                    Finding(
                        "SEMANTIC_REGISTRY_BLOCKER_MISSING",
                        location,
                        "blocked validator requires an explicit blocker",
                    )
                )
    return states, findings


def audit(root: Path) -> tuple[list[Finding], dict[str, Any]]:
    registry, findings = _load_registry(root)
    if registry is None:
        return sorted(set(findings)), {}
    states, registry_findings = _validate_registry(root, registry)
    findings.extend(registry_findings)
    try:
        catalog = validate_contract.load_catalog(root / "contracts")
    except (OSError, ValueError, validate_contract.CatalogError) as exc:
        findings.append(Finding("SEMANTIC_CONTRACT_CATALOG_INVALID", "contracts", str(exc)))
        return sorted(set(findings)), {}

    declarations: list[Declaration] = []
    blocked: set[str] = set()
    for contract in catalog.contracts:
        declaration, declaration_findings = parse_declaration(contract)
        findings.extend(declaration_findings)
        if declaration is None:
            continue
        declarations.append(declaration)
        state = states.get(declaration.validator_id)
        if state is None:
            findings.append(
                Finding(
                    "SEMANTIC_VALIDATOR_UNREGISTERED",
                    f"contracts/{contract.filename}",
                    f"validator {declaration.validator_id!r} is not registered",
                )
            )
            continue
        identity = f"{contract.name}@{contract.version}"
        if state == "blocked":
            blocked.add(identity)
        if declaration.validator_id == "bundle-semantic-dispatcher":
            evaluator = bundle_semantics.builtin_evaluator(contract.name)
            core_owned = all(
                item in bundle_semantics.CORE_OBLIGATION_HANDLERS
                for item in declaration.obligation_ids
            )
            if evaluator is None and not core_owned:
                blocked.add(identity)

    for error in bundle_semantics.builtin_ownership_errors():
        findings.append(
            Finding(
                "SEMANTIC_BUNDLE_OWNERSHIP_INVALID",
                "tools/bundle_semantics.py",
                error,
            )
        )

    report = {
        "schema_version": "1.0",
        "contract_count": len(catalog.contracts),
        "contracts_with_obligations": len(declarations),
        "obligation_count": sum(len(item.obligation_ids) for item in declarations),
        "validators": [
            {
                "validator_id": validator_id,
                "implementation": states[validator_id],
                "contract_count": sum(item.validator_id == validator_id for item in declarations),
            }
            for validator_id in sorted(states)
        ],
        "blocked_contracts": sorted(blocked),
    }
    return sorted(set(findings)), report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root())
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--require-implemented",
        action="store_true",
        help="also fail when any declared contract is runtime blocked",
    )
    args = parser.parse_args(argv)
    findings, report = audit(args.root.resolve())
    if args.require_implemented and report.get("blocked_contracts"):
        findings.append(
            Finding(
                "SEMANTIC_VALIDATOR_IMPLEMENTATION_BLOCKED",
                "blocked-contracts",
                "one or more declared contracts are fail-closed blocked",
            )
        )
    findings = sorted(set(findings))
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(
                {
                    **report,
                    "status": "pass" if not findings else "fail",
                    "findings": [
                        {
                            "code": item.code,
                            "location": item.location,
                            "message": item.message,
                        }
                        for item in findings
                    ],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    if findings:
        for finding in findings:
            print(finding.render(), file=sys.stderr)
        return 2
    print(
        "PASS: semantic obligations are registered; "
        f"{len(report.get('blocked_contracts', []))} contract(s) remain fail-closed blocked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
