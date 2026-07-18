#!/usr/bin/env python3
"""Load and validate the canonical DFT software and skill registry."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
from typing import Any

import yaml


SCHEMA_VERSION = "1.0"
CODE_ID = re.compile(r"^[a-z][a-z0-9-]{1,31}$")
SKILL_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LIFECYCLES = {"active", "experimental", "deprecated"}
INTERFACE_VALUES = {
    "run_manifest": {"required", "unsupported"},
    "postprocess": {"maturity-gated", "unsupported"},
    "campaign_efficiency": {"enabled", "unsupported"},
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def registry_path() -> Path:
    return repo_root() / "registry" / "software-registry.yaml"


def load_registry(path: Path | None = None) -> dict[str, Any]:
    selected = path or registry_path()
    value = yaml.safe_load(selected.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"software registry must be a mapping: {selected}")
    return value


def validation_errors(data: object, source_root: Path | None = None) -> list[str]:
    failures: list[str] = []
    if not isinstance(data, dict):
        return ["<root>: registry must be a mapping"]
    expected_root = {"schema_version", "aggregate_codes", "service_skills", "software"}
    if set(data) != expected_root:
        failures.append(f"<root>: expected fields {sorted(expected_root)}, found {sorted(map(str, data))}")
    if data.get("schema_version") != SCHEMA_VERSION:
        failures.append(f"schema_version: expected {SCHEMA_VERSION!r}")

    aggregates = data.get("aggregate_codes")
    if not isinstance(aggregates, list) or not aggregates:
        failures.append("aggregate_codes: expected a nonempty list")
        aggregates = []
    elif len(set(aggregates)) != len(aggregates):
        failures.append("aggregate_codes: duplicate identifiers are forbidden")
    for code in aggregates:
        if not isinstance(code, str) or not CODE_ID.fullmatch(code):
            failures.append(f"aggregate_codes: invalid code identifier {code!r}")

    services = data.get("service_skills")
    if not isinstance(services, list) or not services:
        failures.append("service_skills: expected a nonempty list")
        services = []
    elif len(set(services)) != len(services):
        failures.append("service_skills: duplicate skill identifiers are forbidden")
    for skill in services:
        if not isinstance(skill, str) or not SKILL_ID.fullmatch(skill):
            failures.append(f"service_skills: invalid skill identifier {skill!r}")

    software = data.get("software")
    if not isinstance(software, dict) or not software:
        failures.append("software: expected a nonempty mapping")
        software = {}
    calculation_skills: list[str] = []
    expected_software_fields = {
        "display_name",
        "calculation_skill",
        "capability_catalog",
        "lifecycle",
        "interfaces",
    }
    for code, specification in software.items():
        location = f"software/{code}"
        if not isinstance(code, str) or not CODE_ID.fullmatch(code):
            failures.append(f"{location}: invalid code identifier")
        if code in aggregates:
            failures.append(f"{location}: code is also declared as an aggregate")
        if not isinstance(specification, dict):
            failures.append(f"{location}: expected a mapping")
            continue
        if set(specification) != expected_software_fields:
            failures.append(
                f"{location}: expected fields {sorted(expected_software_fields)}, "
                f"found {sorted(map(str, specification))}"
            )
        display_name = specification.get("display_name")
        if not isinstance(display_name, str) or not display_name.strip():
            failures.append(f"{location}/display_name: expected a nonempty string")
        skill = specification.get("calculation_skill")
        if not isinstance(skill, str) or not SKILL_ID.fullmatch(skill):
            failures.append(f"{location}/calculation_skill: invalid skill identifier")
        else:
            calculation_skills.append(skill)
        catalog = specification.get("capability_catalog")
        if not isinstance(catalog, dict) or set(catalog) != {"path", "format"}:
            failures.append(f"{location}/capability_catalog: expected path and format")
        else:
            catalog_path = catalog.get("path")
            if (
                not isinstance(catalog_path, str)
                or not catalog_path
                or Path(catalog_path).is_absolute()
                or ".." in Path(catalog_path).parts
            ):
                failures.append(f"{location}/capability_catalog/path: expected a safe relative path")
            if catalog.get("format") not in {"json", "markdown"}:
                failures.append(f"{location}/capability_catalog/format: expected json or markdown")
        if specification.get("lifecycle") not in LIFECYCLES:
            failures.append(f"{location}/lifecycle: unsupported lifecycle")
        interfaces = specification.get("interfaces")
        if not isinstance(interfaces, dict):
            failures.append(f"{location}/interfaces: expected a mapping")
        else:
            if set(interfaces) != set(INTERFACE_VALUES):
                failures.append(
                    f"{location}/interfaces: expected fields {sorted(INTERFACE_VALUES)}, "
                    f"found {sorted(map(str, interfaces))}"
                )
            for name, allowed in INTERFACE_VALUES.items():
                if interfaces.get(name) not in allowed:
                    failures.append(f"{location}/interfaces/{name}: unsupported value {interfaces.get(name)!r}")

    if len(set(calculation_skills)) != len(calculation_skills):
        failures.append("software: calculation_skill values must be unique")
    overlap = set(calculation_skills).intersection(services)
    if overlap:
        failures.append(f"service_skills: calculation skills cannot also be services: {sorted(overlap)}")

    if source_root is not None:
        for skill in calculation_skills + [item for item in services if isinstance(item, str)]:
            if not source_root.joinpath("skills", skill, "SKILL.md").is_file():
                failures.append(f"skills/{skill}: missing registered SKILL.md")
        for code, specification in software.items():
            if not isinstance(specification, dict):
                continue
            skill = specification.get("calculation_skill")
            catalog = specification.get("capability_catalog")
            if isinstance(skill, str) and isinstance(catalog, dict) and isinstance(catalog.get("path"), str):
                path = source_root / "skills" / skill / catalog["path"]
                if not path.is_file():
                    failures.append(f"software/{code}/capability_catalog: missing {path}")
    return failures


def _validated(path: Path | None = None, source_root: Path | None = None) -> dict[str, Any]:
    data = load_registry(path)
    failures = validation_errors(data, source_root)
    if failures:
        raise ValueError("invalid software registry: " + "; ".join(failures))
    return data


def calculation_codes(path: Path | None = None) -> tuple[str, ...]:
    return tuple(_validated(path)["software"])


def aggregate_codes(path: Path | None = None) -> tuple[str, ...]:
    return tuple(_validated(path)["aggregate_codes"])


def all_skill_names(path: Path | None = None) -> tuple[str, ...]:
    data = _validated(path)
    calculations = [entry["calculation_skill"] for entry in data["software"].values()]
    return tuple(calculations + list(data["service_skills"]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path)
    args = parser.parse_args()
    try:
        data = load_registry(args.registry)
        failures = validation_errors(data, repo_root())
    except (OSError, ValueError, yaml.YAMLError) as exc:
        failures = [f"<registry>: {exc}"]
    if failures:
        for item in failures:
            print(item, file=sys.stderr)
        return 2
    print(
        f"PASS: registered {len(data['software'])} calculation codes and "
        f"{len(all_skill_names(args.registry))} skills"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
