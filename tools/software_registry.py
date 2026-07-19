#!/usr/bin/env python3
"""Load and validate software/provider mappings without owning Skill lifecycle."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
from typing import Any

import yaml

from environment_profiles import validation_errors as environment_validation_errors
from registry_yaml import load_yaml_strict


SCHEMA_VERSION = "1.0"
CODE_ID = re.compile(r"^[a-z][a-z0-9-]{1,31}$")
SKILL_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LIFECYCLES = {"active", "experimental", "deprecated"}
PLANNED_LIFECYCLE = "planned"
PLANNED_ROLES = {
    "calculation-engine",
    "postprocess-tool",
    "structure-library",
    "ml-potential-framework",
    "visualization-tool",
    "scientific-workflow-tool",
}
PLANNED_SCOPES = {"dft-core", "dft-adjacent", "extended-chemistry"}
PLANNED_INTEGRATIONS = {"calculation-skill", "postprocess-adapter", "structure-adapter"}
INTEGRATION_BY_ROLE = {
    "calculation-engine": "calculation-skill",
    "postprocess-tool": "postprocess-adapter",
    "structure-library": "structure-adapter",
    "ml-potential-framework": "calculation-skill",
    "visualization-tool": "postprocess-adapter",
    "scientific-workflow-tool": "postprocess-adapter",
}
ACTIVATION_CHECK_IDS = (
    "identity-and-routing",
    "primary-source-provenance",
    "capability-boundary",
    "deterministic-gates",
    "lineage-and-hashes",
    "scientific-gate-separation",
    "shared-interfaces",
    "side-effect-boundary",
    "idempotency-recovery-cancel",
    "validation-evidence",
    "privacy-and-license",
    "portability-and-environment",
    "maintenance-and-forward-test",
)
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
    return load_yaml_strict(selected, "software-registry.yaml")


def _environment_ownership_errors(
    environment_registry: object,
    planned: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    raw_profiles = environment_registry.get("profiles") if isinstance(environment_registry, dict) else None
    if not isinstance(raw_profiles, dict):
        return ["environment-profiles: expected a profiles mapping"]
    for failure in environment_validation_errors(environment_registry):
        failures.append(f"environment-profiles: {failure}")
    profile_owners: dict[str, str] = {}
    for code, specification in planned.items():
        if not isinstance(specification, dict):
            continue
        role = specification.get("role")
        environment = specification.get("environment_profiles")
        profile_ids = environment.get("profile_ids") if isinstance(environment, dict) else None
        if not isinstance(profile_ids, list):
            continue
        for profile_id in profile_ids:
            profile = raw_profiles.get(profile_id)
            if not isinstance(profile, dict):
                failures.append(
                    f"planned_software/{code}/environment_profiles: unknown profile {profile_id!r}"
                )
            elif profile.get("role") != role:
                failures.append(
                    f"planned_software/{code}/environment_profiles: profile {profile_id!r} "
                    f"has role {profile.get('role')!r}, expected {role!r}"
                )
            if profile_id in profile_owners:
                failures.append(
                    f"planned_software/{code}/environment_profiles: profile {profile_id!r} "
                    f"is already owned by {profile_owners[profile_id]!r}"
                )
            else:
                profile_owners[profile_id] = code
    unowned_profiles = set(raw_profiles).difference(profile_owners)
    if unowned_profiles:
        failures.append(
            "environment-profiles: profiles must have exactly one planned software owner; "
            f"unowned {sorted(unowned_profiles)!r}"
        )
    return failures


def validation_errors(
    data: object,
    source_root: Path | None = None,
    environment_data: dict[str, Any] | None = None,
) -> list[str]:
    failures: list[str] = []
    if not isinstance(data, dict):
        return ["<root>: registry must be a mapping"]
    expected_root = {
        "schema_version",
        "aggregate_codes",
        "software",
        "planned_software",
    }
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
    planned = data.get("planned_software")
    if not isinstance(planned, dict) or not planned:
        failures.append("planned_software: expected a nonempty mapping")
        planned = {}
    expected_planned_fields = {
        "display_name",
        "role",
        "scope",
        "intended_integration",
        "intended_skill",
        "activation_profile",
        "environment_profiles",
        "required_check_ids",
        "lifecycle",
    }
    for code, specification in planned.items():
        location = f"planned_software/{code}"
        if not isinstance(code, str) or not CODE_ID.fullmatch(code):
            failures.append(f"{location}: invalid code identifier")
        if code in aggregates or code in software:
            failures.append(f"{location}: identifier collides with an active or aggregate code")
        if not isinstance(specification, dict):
            failures.append(f"{location}: expected a mapping")
            continue
        if set(specification) != expected_planned_fields:
            failures.append(
                f"{location}: expected fields {sorted(expected_planned_fields)}, "
                f"found {sorted(map(str, specification))}"
            )
        display_name = specification.get("display_name")
        if not isinstance(display_name, str) or not display_name.strip():
            failures.append(f"{location}/display_name: expected a nonempty string")
        if specification.get("role") not in PLANNED_ROLES:
            failures.append(f"{location}/role: unsupported role {specification.get('role')!r}")
        if specification.get("scope") not in PLANNED_SCOPES:
            failures.append(f"{location}/scope: unsupported scope {specification.get('scope')!r}")
        intended_integration = specification.get("intended_integration")
        if intended_integration not in PLANNED_INTEGRATIONS:
            failures.append(
                f"{location}/intended_integration: unsupported value "
                f"{intended_integration!r}"
            )
        skill = specification.get("intended_skill")
        if not isinstance(skill, str) or not SKILL_ID.fullmatch(skill):
            failures.append(f"{location}/intended_skill: invalid skill identifier")
        role = specification.get("role")
        profile = specification.get("activation_profile")
        if profile != role:
            failures.append(
                f"{location}/activation_profile: must equal provider role {role!r}, found {profile!r}"
            )
        expected_integration = INTEGRATION_BY_ROLE.get(role)
        if expected_integration is not None and intended_integration != expected_integration:
            failures.append(
                f"{location}/intended_integration: role {role!r} requires {expected_integration!r}"
            )
        environment = specification.get("environment_profiles")
        if not isinstance(environment, dict) or set(environment) != {"selection_policy", "profile_ids"}:
            failures.append(
                f"{location}/environment_profiles: expected selection_policy and profile_ids"
            )
            environment = {}
        if environment.get("selection_policy") not in {
            "all_of",
            "any_of",
            "platform_variant",
            "edition_variant",
        }:
            failures.append(f"{location}/environment_profiles/selection_policy: unsupported value")
        environment_profile_ids = environment.get("profile_ids")
        if not isinstance(environment_profile_ids, list) or not environment_profile_ids:
            failures.append(f"{location}/environment_profiles/profile_ids: expected a nonempty list")
            environment_profile_ids = []
        elif len(environment_profile_ids) != len(set(environment_profile_ids)):
            failures.append(f"{location}/environment_profiles/profile_ids: duplicate identifiers are forbidden")
        for index, profile_id in enumerate(environment_profile_ids):
            if not isinstance(profile_id, str) or not CODE_ID.fullmatch(profile_id):
                failures.append(
                    f"{location}/environment_profiles/profile_ids/{index}: invalid environment profile identifier"
                )
        required_check_ids = specification.get("required_check_ids")
        if required_check_ids != list(ACTIVATION_CHECK_IDS):
            failures.append(f"{location}/required_check_ids: must equal the 13 fixed activation checks")
        if specification.get("lifecycle") != PLANNED_LIFECYCLE:
            failures.append(f"{location}/lifecycle: expected {PLANNED_LIFECYCLE!r}")

    if source_root is not None:
        for skill in calculation_skills:
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
    selected_environment = environment_data
    if selected_environment is None and source_root is not None:
        environment_registry_path = source_root / "registry" / "environment-profiles.yaml"
        try:
            selected_environment = load_yaml_strict(
                environment_registry_path, "environment-profiles.yaml"
            )
        except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
            failures.append(f"environment-profiles: cannot load registry: {exc}")
    if selected_environment is not None:
        failures.extend(_environment_ownership_errors(selected_environment, planned))
    return failures


def _validated(path: Path | None = None, source_root: Path | None = None) -> dict[str, Any]:
    data = load_registry(path)
    failures = validation_errors(data, source_root)
    if failures:
        raise ValueError("invalid software registry: " + "; ".join(failures))
    return data


def calculation_codes(path: Path | None = None) -> tuple[str, ...]:
    return tuple(
        code
        for code, specification in _validated(path)["software"].items()
        if specification["lifecycle"] == "active"
    )


def aggregate_codes(path: Path | None = None) -> tuple[str, ...]:
    return tuple(_validated(path)["aggregate_codes"])


def planned_software_codes(path: Path | None = None) -> tuple[str, ...]:
    """Return roadmap identifiers without promoting them to supported codes."""

    return tuple(_validated(path)["planned_software"])


def planned_skill_names(path: Path | None = None) -> tuple[str, ...]:
    """Return de-duplicated intended skills in roadmap declaration order."""

    names: list[str] = []
    for entry in _validated(path)["planned_software"].values():
        name = entry["intended_skill"]
        if name not in names:
            names.append(name)
    return tuple(names)


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
        f"PASS: registered {len(data['software'])} active calculation codes, "
        f"{len(data['planned_software'])} planned software/provider mappings"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
