#!/usr/bin/env python3
"""Audit repository-wide DFT skill registration and extension boundaries."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Any

from audit_hygiene import audit_repository as audit_repository_hygiene
from skill_registry import planned_skill_names, validate_active_sources
from registry_snapshot import RegistrySnapshot, RegistrySnapshotError, load_registry_snapshot
from software_registry import repo_root
from sync_contract_codes import CONTRACT_CODE_KINDS
from validate_contract import CatalogError, load_catalog
import strict_json


TARGET_ENV = "VIBE_DFT_SKILLS_TARGET"


def capability_catalog_errors(path: Path) -> list[str]:
    """Validate one JSON capability catalog through the shared trust boundary."""

    try:
        value = strict_json.load_object(path, path.name)
    except OSError as exc:
        return [f"unreadable: {exc.__class__.__name__}"]
    except strict_json.StrictJSONError as exc:
        return [str(exc)]
    failures: list[str] = []
    if value.get("schema_version") != "1.0":
        failures.append("expected schema_version '1.0'")
    if not isinstance(value.get("profiles"), dict) or not value["profiles"]:
        failures.append("expected a nonempty profiles mapping")
    return failures


def _snapshot_contract_drift(
    snapshot: RegistrySnapshot,
    catalog: Any,
) -> list[str]:
    failures: list[str] = []
    calculation = list(snapshot.calculation_codes())
    aggregate = [*calculation, *snapshot.aggregate_codes()]
    for filename, kind in CONTRACT_CODE_KINDS.items():
        contract = catalog.by_filename.get(filename)
        if contract is None:
            failures.append(f"{filename}: schema is absent from the validated catalog")
            continue
        try:
            actual = contract.schema["properties"]["code"]["enum"]
        except (KeyError, TypeError):
            failures.append(f"{filename}: cannot read code enum from validated schema")
            continue
        expected = calculation if kind == "calculation" else aggregate
        if actual != expected:
            failures.append(f"{filename}: code enum {actual!r} != registry {expected!r}")
    return failures


def repository_audit(
    root: Path | None = None,
) -> tuple[list[str], RegistrySnapshot | None]:
    """Return findings plus the one fully validated registry snapshot, if any."""

    selected_root = (root or repo_root()).resolve()
    failures: list[str] = []

    try:
        catalog = load_catalog(selected_root / "contracts")
    except (OSError, ValueError, CatalogError) as exc:
        failures.append(f"contract-catalog: {exc}")
        catalog = None

    try:
        snapshot = load_registry_snapshot(selected_root, validate_sources=True)
    except (OSError, RegistrySnapshotError, ValueError) as exc:
        failures.append(f"registry-snapshot: {exc}")
        snapshot = None

    if snapshot is not None:
        expected_skills = {
            name
            for name, entry in snapshot.skills["skills"].items()
            if entry["lifecycle"] in {"active", "development"}
        }
        try:
            actual_skills = {
                path.name
                for path in selected_root.joinpath("skills").iterdir()
                if path.is_dir() and path.joinpath("SKILL.md").is_file()
            }
        except OSError as exc:
            failures.append(f"skills: source directory is unavailable ({exc.__class__.__name__})")
            actual_skills = set()
        if actual_skills != expected_skills:
            failures.append(
                f"skills: registered {sorted(expected_skills)!r} != repository {sorted(actual_skills)!r}"
            )

        if catalog is not None:
            failures.extend(_snapshot_contract_drift(snapshot, catalog))

        for code, specification in snapshot.software["software"].items():
            capability = specification["capability_catalog"]
            if capability["format"] != "json":
                continue
            path = (
                selected_root
                / "skills"
                / specification["calculation_skill"]
                / capability["path"]
            )
            failures.extend(
                f"software/{code}/capability_catalog: {failure}"
                for failure in capability_catalog_errors(path)
            )

        scripts = selected_root / "skills" / "dft-postprocess" / "scripts"
        sys.path.insert(0, str(scripts))
        try:
            from dftpost.registry import load_registry as load_observables
            from dftpost.registry import validate_registry as validate_observables

            observable_registry = load_observables()
            for failure in validate_observables(observable_registry, snapshot=snapshot):
                failures.append(f"observable-registry: {failure}")
            expected_codes = set(snapshot.calculation_codes())
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

    skill_data = snapshot.skills if snapshot is not None else None
    for finding in audit_repository_hygiene(selected_root, skill_data=skill_data):
        failures.append(f"hygiene: {finding.render()}")
    return failures, snapshot


def repository_errors(root: Path | None = None) -> list[str]:
    failures, _ = repository_audit(root)
    return failures


def installed_errors(root: Path | None = None, target: Path | None = None) -> list[str]:
    selected_root = root or repo_root()
    selected_target = target
    if selected_target is None:
        configured = os.environ.get(TARGET_ENV)
        if not configured:
            return [f"installed: pass --installed-root or set {TARGET_ENV}"]
        selected_target = Path(configured).expanduser()
    failures: list[str] = []
    skill_registry_path = selected_root / "registry" / "skill-registry.yaml"
    try:
        active_names = validate_active_sources(selected_root)
    except ValueError as exc:
        return [f"installed/skill-registry: {exc}"]
    for name in active_names:
        expected = selected_root / "skills" / name
        installed = selected_target / name
        if not installed.is_symlink():
            state = "missing" if not installed.exists() else "not a symlink"
            failures.append(f"installed/{name}: {state} at {installed}")
        elif installed.resolve() != expected.resolve():
            failures.append(f"installed/{name}: points to {installed.resolve()}, expected {expected}")
    for name in planned_skill_names(skill_registry_path):
        installed = selected_target / name
        if installed.exists() or installed.is_symlink():
            failures.append(f"installed/{name}: planned Skill must not be present at {installed}")
    skills_root = (selected_root / "skills").resolve()
    active = set(active_names)
    if selected_target.is_dir():
        for installed in selected_target.iterdir():
            if installed.name in active or not installed.is_symlink():
                continue
            try:
                resolved = installed.resolve()
                resolved.relative_to(skills_root)
            except (OSError, ValueError):
                continue
            failures.append(
                f"installed/{installed.name}: stale repository Skill symlink points to non-active source {resolved}"
            )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-installed", action="store_true")
    parser.add_argument("--installed-root", type=Path)
    args = parser.parse_args()
    failures, snapshot = repository_audit()
    if args.check_installed:
        failures.extend(installed_errors(target=args.installed_root))
    if failures:
        for item in failures:
            print(item, file=sys.stderr)
        return 2
    if snapshot is None:  # Defensive: success must always carry the validated truth snapshot.
        print("registry-snapshot: validated snapshot is unavailable", file=sys.stderr)
        return 2
    print(
        f"PASS: repository interfaces align across {len(snapshot.calculation_codes())} codes and "
        f"{sum(item['lifecycle'] == 'active' for item in snapshot.skills['skills'].values())} "
        "active skills and "
        f"{sum(item['lifecycle'] == 'development' for item in snapshot.skills['skills'].values())} "
        "development skills"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
