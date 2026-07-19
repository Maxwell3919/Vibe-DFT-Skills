#!/usr/bin/env python3
"""Search pinned Phonopy documentation and emit non-executing recipe plans."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "references" / "official-command-catalog.json"
RECIPES_PATH = ROOT / "references" / "task-recipes.json"
MAX_JSON_BYTES = 2_000_000


class CatalogError(Exception):
    """Raised when pinned catalog data or a request is invalid."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise CatalogError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise CatalogError(f"cannot read {path.name}: {exc}") from exc
    if not raw or len(raw) > MAX_JSON_BYTES:
        raise CatalogError(f"{path.name} is empty or too large")
    try:
        text = raw.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda token: (_ for _ in ()).throw(
                CatalogError(f"invalid JSON constant: {token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, CatalogError) as exc:
        raise CatalogError(f"invalid {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise CatalogError(f"{path.name} root must be an object")
    return value


def load_data() -> tuple[dict[str, Any], dict[str, Any]]:
    catalog = _load_json(CATALOG_PATH)
    recipes = _load_json(RECIPES_PATH)
    for value, label in ((catalog, "catalog"), (recipes, "recipes")):
        if value.get("schema_version") != "1.0" or value.get("software") != "phonopy":
            raise CatalogError(f"unsupported {label} identity")
        if value.get("documentation_version") != "4.3.1":
            raise CatalogError(f"unsupported {label} documentation version")
    return catalog, recipes


def _catalog_records(
    catalog: dict[str, Any], recipes: dict[str, Any]
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    sections = (
        ("entrypoint", "entrypoints"),
        ("capability", "capabilities"),
        ("option-group", "option_groups"),
        ("calculator-interface", "calculator_interfaces"),
        ("documentation-conflict", "documentation_conflicts"),
    )
    for kind, key in sections:
        values = catalog.get(key)
        if not isinstance(values, list):
            raise CatalogError(f"catalog {key} must be an array")
        for item in values:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                raise CatalogError(f"invalid {kind} record")
            records.append({"kind": kind, **item})
    recipe_map = recipes.get("recipes")
    if not isinstance(recipe_map, dict):
        raise CatalogError("recipes must be an object")
    for recipe_id, recipe in recipe_map.items():
        if not isinstance(recipe_id, str) or not isinstance(recipe, dict):
            raise CatalogError("invalid recipe record")
        records.append({"kind": "recipe", "id": recipe_id, **recipe})
    identities = [(item["kind"], item["id"].casefold()) for item in records]
    if len(identities) != len(set(identities)):
        raise CatalogError("duplicate record identity within a catalog kind")
    return records


def kinds_report(catalog: dict[str, Any], recipes: dict[str, Any]) -> dict[str, Any]:
    records = _catalog_records(catalog, recipes)
    counts: dict[str, int] = {}
    for record in records:
        counts[record["kind"]] = counts.get(record["kind"], 0) + 1
    return {
        "status": "pass",
        "operation": "kinds",
        "documentation_version": catalog["documentation_version"],
        "counts": counts,
        "native_execution_performed": False,
    }


def list_report(
    catalog: dict[str, Any], recipes: dict[str, Any], kind: str | None
) -> dict[str, Any]:
    records = _catalog_records(catalog, recipes)
    selected = [item for item in records if kind is None or item["kind"] == kind]
    if kind is not None and not selected:
        raise CatalogError(f"unknown or empty kind: {kind}")
    return {
        "status": "pass",
        "operation": "list",
        "kind_filter": kind,
        "count": len(selected),
        "records": selected,
        "native_execution_performed": False,
    }


def search_report(
    catalog: dict[str, Any], recipes: dict[str, Any], query: str
) -> dict[str, Any]:
    needle = " ".join(query.casefold().replace("_", " ").replace("-", " ").split())
    if not needle:
        raise CatalogError("search query must not be empty")
    matches = []
    for item in _catalog_records(catalog, recipes):
        haystack = " ".join(
            json.dumps(item, ensure_ascii=False, sort_keys=True)
            .casefold()
            .replace("_", " ")
            .replace("-", " ")
            .split()
        )
        if needle in haystack:
            matches.append(item)
    return {
        "status": "pass",
        "operation": "search",
        "query": query,
        "count": len(matches),
        "records": matches,
        "native_execution_performed": False,
    }


def show_report(
    catalog: dict[str, Any], recipes: dict[str, Any], record_id: str
) -> dict[str, Any]:
    matches = [
        item
        for item in _catalog_records(catalog, recipes)
        if item["id"].casefold() == record_id.casefold()
    ]
    if not matches:
        raise CatalogError(f"unknown catalog id: {record_id}")
    if len(matches) > 1:
        raise CatalogError(f"ambiguous catalog id: {record_id}")
    return {
        "status": "pass",
        "operation": "show",
        "record": matches[0],
        "native_validation": catalog["native_validation"],
        "native_execution_performed": False,
    }


def plan_report(
    catalog: dict[str, Any], recipes: dict[str, Any], recipe_id: str
) -> tuple[dict[str, Any], int]:
    recipe_map = recipes["recipes"]
    base = {
        "operation": "plan",
        "recipe": recipe_id,
        "documentation_version": catalog["documentation_version"],
        "native_validation": catalog["native_validation"],
        "execution_authorized": False,
        "native_execution_performed": False,
        "recipe_reference": "references/calling-and-recipes.md",
    }
    if recipe_id not in recipe_map:
        base.update(
            {
                "status": "blocked",
                "finding": "PHONOPY_RECIPE_NOT_ESTABLISHED",
                "message": "The official catalog can list a feature without establishing a version-safe recipe.",
            }
        )
        return base, 3
    recipe = recipe_map[recipe_id]
    base.update(
        {
            "status": "documentation-plan",
            "evidence_status": recipe["status"],
            "commands": recipe["commands"],
            "checks": recipe["checks"],
            "caution": recipe["caution"],
            "source": recipe["source"],
        }
    )
    return base, 0


def probe_report() -> dict[str, Any]:
    executable_names = [
        "phonopy",
        "phonopy-init",
        "phonopy-load",
        "phonopy-bandplot",
        "phonopy-calc-convert",
        "phonopy-crystal-born",
        "phonopy-gruneisen",
        "phonopy-gruneisenplot",
        "phonopy-pdosplot",
        "phonopy-propplot",
        "phonopy-qha",
        "phonopy-tdplot",
        "phonopy-vasp-born",
        "phonopy-vasp-efe",
        "phonopy-qe-born",
    ]
    resolved = {name: shutil.which(name) for name in executable_names}
    try:
        package_version: str | None = importlib.metadata.version("phonopy")
    except importlib.metadata.PackageNotFoundError:
        package_version = None
    available = any(resolved.values()) or package_version is not None
    return {
        "status": "available-unverified" if available else "tool-unavailable",
        "operation": "probe",
        "executables": resolved,
        "python_distribution_version": package_version,
        "help_or_version_executed": False,
        "native_execution_performed": False,
        "scientific_capability_claim": "none",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    subparsers.add_parser("kinds")
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--kind")
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    show_parser = subparsers.add_parser("show")
    show_parser.add_argument("record_id")
    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("recipe_id")
    subparsers.add_parser("probe")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        if args.operation == "probe":
            report, code = probe_report(), 0
        else:
            catalog, recipes = load_data()
            if args.operation == "kinds":
                report, code = kinds_report(catalog, recipes), 0
            elif args.operation == "list":
                report, code = list_report(catalog, recipes, args.kind), 0
            elif args.operation == "search":
                report, code = search_report(catalog, recipes, args.query), 0
            elif args.operation == "show":
                report, code = show_report(catalog, recipes, args.record_id), 0
            else:
                report, code = plan_report(catalog, recipes, args.recipe_id)
    except CatalogError as exc:
        report, code = {
            "status": "error",
            "finding": "PHONOPY_CATALOG_ERROR",
            "message": str(exc),
            "native_execution_performed": False,
        }, 2
    json.dump(report, sys.stdout, ensure_ascii=False, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
