#!/usr/bin/env python3
"""Audit repository-wide DFT skill registration and extension boundaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from software_registry import all_skill_names, calculation_codes, load_registry, repo_root, validation_errors
from sync_contract_codes import contract_drift


def repository_errors(root: Path | None = None) -> list[str]:
    selected_root = root or repo_root()
    failures: list[str] = []
    try:
        software = load_registry(selected_root / "registry" / "software-registry.yaml")
        failures.extend(validation_errors(software, selected_root))
        expected_skills = set(all_skill_names(selected_root / "registry" / "software-registry.yaml"))
    except (OSError, ValueError) as exc:
        return [f"software-registry: {exc}"]

    actual_skills = {
        path.name
        for path in selected_root.joinpath("skills").iterdir()
        if path.is_dir() and path.joinpath("SKILL.md").is_file()
    }
    if actual_skills != expected_skills:
        failures.append(
            f"skills: registered {sorted(expected_skills)!r} != repository {sorted(actual_skills)!r}"
        )
    failures.extend(contract_drift(selected_root))

    for code, specification in software["software"].items():
        catalog = specification["capability_catalog"]
        if catalog["format"] != "json":
            continue
        path = selected_root / "skills" / specification["calculation_skill"] / catalog["path"]
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"software/{code}/capability_catalog: {exc}")
            continue
        if not isinstance(value, dict) or value.get("schema_version") != "1.0":
            failures.append(f"software/{code}/capability_catalog: expected schema_version '1.0'")
        if not isinstance(value.get("profiles"), dict) or not value["profiles"]:
            failures.append(f"software/{code}/capability_catalog: expected a nonempty profiles mapping")

    scripts = selected_root / "skills" / "dft-postprocess" / "scripts"
    sys.path.insert(0, str(scripts))
    try:
        from dftpost.registry import load_registry as load_observables
        from dftpost.registry import validate_registry as validate_observables

        observable_registry = load_observables()
        for failure in validate_observables(observable_registry):
            failures.append(f"observable-registry: {failure}")
        expected_codes = set(calculation_codes(selected_root / "registry" / "software-registry.yaml"))
        observables = observable_registry.get("observables", {})
        if isinstance(observables, dict):
            for observable_id, observable in observables.items():
                if not isinstance(observable, dict) or not isinstance(observable.get("codes"), dict):
                    continue
                actual_codes = set(observable["codes"])
                if actual_codes != expected_codes:
                    failures.append(
                        f"observable-registry: observables/{observable_id}/codes "
                        f"{sorted(actual_codes)!r} != registered {sorted(expected_codes)!r}"
                    )
    except (ImportError, OSError, ValueError) as exc:
        failures.append(f"observable-registry: {exc}")
    finally:
        try:
            sys.path.remove(str(scripts))
        except ValueError:
            pass
    return failures


def installed_errors(root: Path | None = None, target: Path | None = None) -> list[str]:
    selected_root = root or repo_root()
    selected_target = target or Path.home() / ".codex" / "skills"
    failures: list[str] = []
    for name in all_skill_names(selected_root / "registry" / "software-registry.yaml"):
        expected = selected_root / "skills" / name
        installed = selected_target / name
        if not installed.is_symlink():
            state = "missing" if not installed.exists() else "not a symlink"
            failures.append(f"installed/{name}: {state} at {installed}")
        elif installed.resolve() != expected.resolve():
            failures.append(f"installed/{name}: points to {installed.resolve()}, expected {expected}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-installed", action="store_true")
    parser.add_argument("--installed-root", type=Path)
    args = parser.parse_args()
    failures = repository_errors()
    if args.check_installed:
        failures.extend(installed_errors(target=args.installed_root))
    if failures:
        for item in failures:
            print(item, file=sys.stderr)
        return 2
    print(
        f"PASS: repository interfaces align across {len(calculation_codes())} codes and "
        f"{len(all_skill_names())} skills"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
