#!/usr/bin/env python3
"""Validate non-active Skill weak-model decision tables fail closed."""

from __future__ import annotations

import argparse
from functools import lru_cache
from pathlib import Path
import sys
from typing import Any

from jsonschema import Draft202012Validator

from registry_yaml import RegistryYAMLError, load_yaml_strict
import strict_json
import validate_contract


CONTRACT = "candidate-decision-table"
RELATIVE_TABLE = Path("references/weak-model-decision-table.json")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def _prepared_contract_validator() -> Draft202012Validator:
    catalog = validate_contract.load_catalog()
    contract = catalog.resolve(CONTRACT)
    return Draft202012Validator(
        contract.schema,
        registry=catalog.registry,
        format_checker=validate_contract.FORMAT_CHECKER,
    )


def _schema_errors(
    value: object,
    prepared: Draft202012Validator,
) -> list[str]:
    try:
        discovered = list(prepared.iter_errors(value))
    except Exception as exc:
        return [f"<schema>: validation could not resolve locally: {exc}"]
    failures: list[str] = []
    for error in sorted(
        discovered,
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    ):
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        failures.append(f"{location}: {error.message}")
    return failures


def semantic_errors(
    value: object,
    *,
    expected_skill_id: str | None = None,
    expected_lifecycle: str | None = None,
    prepared: Draft202012Validator | None = None,
) -> list[str]:
    """Return deterministic cross-field failures after JSON Schema validation."""

    if prepared is None:
        try:
            prepared = _prepared_contract_validator()
        except (OSError, ValueError, validate_contract.CatalogError) as exc:
            return [f"<catalog>: {exc}"]
    failures = _schema_errors(value, prepared)
    if failures or not isinstance(value, dict):
        return failures

    skill_id = value["skill_id"]
    if expected_skill_id is not None and skill_id != expected_skill_id:
        failures.append(
            f"skill_id: declared {skill_id!r} != candidate directory {expected_skill_id!r}"
        )
    if expected_lifecycle is not None and value["lifecycle"] != expected_lifecycle:
        failures.append(
            f"lifecycle: declared {value['lifecycle']!r} != registry lifecycle {expected_lifecycle!r}"
        )

    cases = value["cases"]
    case_ids = [item["case_id"] for item in cases]
    priorities = [item["priority"] for item in cases]
    actions = [item["minimum_next_action"] for item in cases]

    if len(set(case_ids)) != len(case_ids):
        failures.append("cases: case_id values must be unique")
    if len(set(priorities)) != len(priorities):
        failures.append("cases: priority values must be unique")
    expected_priorities = list(range(1, len(cases) + 1))
    if priorities != expected_priorities:
        failures.append(
            "cases: array order and priorities must be exactly "
            f"{expected_priorities!r}, found {priorities!r}"
        )
    if len(set(actions)) != len(actions):
        failures.append("cases: minimum_next_action values must be unique")

    default_case_id = value["default_case_id"]
    if default_case_id not in case_ids:
        failures.append("default_case_id: must identify one declared case")
    elif default_case_id != case_ids[-1]:
        failures.append("default_case_id: the default case must be the final priority")

    for index, item in enumerate(cases):
        location = f"cases/{index}"
        if item["action_state"] == "local_gate_blocked" and not item["finding_codes"]:
            failures.append(
                f"{location}/finding_codes: a blocked case requires at least one stable finding code"
            )
        if item["case_id"] == default_case_id:
            if item["action_state"] not in {"needs_evidence", "local_gate_blocked"}:
                failures.append(
                    f"{location}/action_state: default case must fail closed"
                )
            if item["required_evidence"]:
                failures.append(
                    f"{location}/required_evidence: default case cannot depend on evidence"
                )

    return failures


def validate_file(
    path: Path,
    *,
    expected_skill_id: str | None = None,
    expected_lifecycle: str | None = None,
    prepared: Draft202012Validator | None = None,
) -> list[str]:
    try:
        value = strict_json.load_object(
            path,
            path.name,
            max_bytes=512 * 1024,
            max_nodes=20_000,
            max_depth=32,
            max_string_chars=4_000,
            max_number_chars=32,
        )
    except (OSError, strict_json.StrictJSONError) as exc:
        return [f"<file>: STRICT_JSON_INVALID {path.name}: {exc}"]
    return semantic_errors(
        value,
        expected_skill_id=expected_skill_id,
        expected_lifecycle=expected_lifecycle,
        prepared=prepared,
    )


def development_skill_ids(root: Path) -> tuple[str, ...]:
    registry_path = root / "registry" / "skill-registry.yaml"
    value = load_yaml_strict(registry_path, "skill-registry.yaml")
    skills = value.get("skills")
    if not isinstance(skills, dict):
        raise RegistryYAMLError("skill-registry.yaml: skills must be a mapping")
    return tuple(
        skill_id
        for skill_id, entry in skills.items()
        if isinstance(skill_id, str)
        and isinstance(entry, dict)
        and entry.get("lifecycle") == "development"
    )


def validate_all_development(root: Path) -> list[str]:
    failures: list[str] = []
    try:
        skill_ids = development_skill_ids(root)
    except (OSError, ValueError, RegistryYAMLError) as exc:
        return [f"<registry>: {exc}"]
    try:
        prepared = _prepared_contract_validator()
    except (OSError, ValueError, validate_contract.CatalogError) as exc:
        return [f"<catalog>: {exc}"]

    for skill_id in skill_ids:
        path = root / "skills" / skill_id / RELATIVE_TABLE
        if not path.is_file():
            failures.append(
                f"{skill_id}: missing skills/{skill_id}/{RELATIVE_TABLE.as_posix()}"
            )
            continue
        failures.extend(
            f"{skill_id}: {item}"
            for item in validate_file(
                path,
                expected_skill_id=skill_id,
                expected_lifecycle="development",
                prepared=prepared,
            )
        )
    return failures


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=Path, help="validate one table")
    group.add_argument(
        "--all-development",
        action="store_true",
        help="validate the canonical table for every development Skill",
    )
    parser.add_argument(
        "--skill-id",
        help="expected candidate directory identity when validating one table",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=repo_root(),
        help="repository root for --all-development",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.all_development:
        failures = validate_all_development(args.root.resolve())
        label = "all development decision tables"
    else:
        failures = validate_file(args.file, expected_skill_id=args.skill_id)
        label = args.file.name
    if failures:
        for item in failures:
            print(item, file=sys.stderr)
        return 2
    print(f"PASS: {label} matches the fail-closed candidate decision-table contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
