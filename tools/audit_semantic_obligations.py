#!/usr/bin/env python3
"""Audit Schema semantic-obligation declarations against registered validator ownership."""

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
OBLIGATION_ID = re.compile(r"^(?:[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*|[a-z][a-z0-9]*(?:-[a-z0-9]+)*)$")
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


def parse_declaration(contract: validate_contract.ContractSchema) -> tuple[Declaration | None, list[Finding]]:
    raw = contract.schema.get("x-vibe-semantic-obligations")
    location = f"contracts/{contract.filename}/x-vibe-semantic-obligations"
    if raw is None:
        return None, []
    findings: list[Finding] = []
    validator_id: object
    obligations: object
    form: str
    if isinstance(raw, list):
        validator_id = "bundle-semantic-dispatcher"
        obligations = raw
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
        findings.append(
            Finding(
                "SEMANTIC_DECLARATION_INVALID",
                location,
                "declaration must be a list or an object",
            )
        )
        return None, findings

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
        if not isinstance(obligation, str) or OBLIGATION_ID.fullmatch(obligation) is None:
            findings.append(
                Finding(
                    "SEMANTIC_OBLIGATION_ID_INVALID",
                    f"{location}/{index}",
                    f"invalid obligation ID {obligation!r}",
                )
            )
            continue
        normalized.append(obligation)
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
        findings,
    )


def _load_registry(root: Path) -> tuple[dict[str, Any] | None, list[Finding]]:
    path = root / "registry" / "semantic-obligations.yaml"
    try:
        value = load_yaml_strict(path)
    except (OSError, UnicodeError, RegistryYAMLError) as exc:
        return None, [
            Finding(
                "SEMANTIC_REGISTRY_UNREADABLE",
                path.relative_to(root).as_posix(),
                str(exc),
            )
        ]
    if not isinstance(value, dict) or value.get("schema_version") != "1.0":
        return None, [
            Finding(
                "SEMANTIC_REGISTRY_SCHEMA_INVALID",
                "registry/semantic-obligations.yaml",
                "schema_version must be 1.0",
            )
        ]
    return value, []


def audit(root: Path) -> tuple[list[Finding], dict[str, Any]]:
    findings: list[Finding] = []
    registry, registry_findings = _load_registry(root)
    findings.extend(registry_findings)
    if registry is None:
        return sorted(set(findings)), {}

    validators = registry.get("validators")
    policies = registry.get("policies")
    if not isinstance(validators, dict) or not validators:
        findings.append(
            Finding(
                "SEMANTIC_REGISTRY_VALIDATORS_INVALID",
                "registry/semantic-obligations.yaml/validators",
                "validators must be a nonempty mapping",
            )
        )
        validators = {}
    if not isinstance(policies, dict):
        findings.append(
            Finding(
                "SEMANTIC_REGISTRY_POLICIES_INVALID",
                "registry/semantic-obligations.yaml/policies",
                "policies must be a mapping",
            )
        )

    validator_states: dict[str, str] = {}
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
        validator_states[validator_id] = str(state)
        ceiling = specification.get("maximum_claim_when_unavailable")
        if ceiling not in CLAIM_CEILINGS:
            findings.append(
                Finding(
                    "SEMANTIC_REGISTRY_CLAIM_CEILING_INVALID",
                    location,
                    f"invalid unavailable claim ceiling {ceiling!r}",
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

    try:
        catalog = validate_contract.load_catalog(root / "contracts")
    except (OSError, ValueError, validate_contract.CatalogError) as exc:
        findings.append(
            Finding(
                "SEMANTIC_CONTRACT_CATALOG_INVALID",
                "contracts",
                str(exc),
            )
        )
        return sorted(set(findings)), {}

    declarations: list[Declaration] = []
    for contract in catalog.contracts:
        declaration, declaration_findings = parse_declaration(contract)
        findings.extend(declaration_findings)
        if declaration is not None:
            declarations.append(declaration)
            state = validator_states.get(declaration.validator_id)
            if state is None:
                findings.append(
                    Finding(
                        "SEMANTIC_VALIDATOR_UNREGISTERED",
                        f"contracts/{contract.filename}",
                        f"validator {declaration.validator_id!r} is not registered",
                    )
                )
            if declaration.validator_id == "bundle-semantic-dispatcher":
                evaluator = bundle_semantics.builtin_evaluator(contract.name)
                core_owned = all(
                    obligation in bundle_semantics.CORE_OBLIGATION_HANDLERS
                    for obligation in declaration.obligation_ids
                )
                if evaluator is None and not core_owned:
                    findings.append(
                        Finding(
                            "SEMANTIC_BUNDLE_OWNER_MISSING",
                            f"contracts/{contract.filename}",
                            "list-form obligations have no exact repository-owned evaluator",
                        )
                    )

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
                "implementation": validator_states[validator_id],
                "contract_count": sum(
                    item.validator_id == validator_id for item in declarations
                ),
            }
            for validator_id in sorted(validator_states)
        ],
        "blocked_contracts": sorted(
            f"{item.contract_name}@{item.schema_version}"
            for item in declarations
            if validator_states.get(item.validator_id) == "blocked"
        ),
    }
    return sorted(set(findings)), report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root())
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--require-implemented",
        action="store_true",
        help="also fail when any declared validator is registered as blocked",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    findings, report = audit(root)
    if args.require_implemented:
        for item in report.get("validators", []):
            if item.get("implementation") == "blocked" and item.get("contract_count", 0):
                findings.append(
                    Finding(
                        "SEMANTIC_VALIDATOR_IMPLEMENTATION_BLOCKED",
                        f"validator/{item.get('validator_id')}",
                        "declared contracts depend on a blocked validator",
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
    blocked = len(report.get("blocked_contracts", []))
    print(
        "PASS: semantic obligations are registered and owned; "
        f"{blocked} contract(s) remain explicitly blocked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
