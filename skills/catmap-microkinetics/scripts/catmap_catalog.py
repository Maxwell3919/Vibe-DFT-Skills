#!/usr/bin/env python3
"""Search CatMAP's versioned documentation catalog without importing CatMAP.

The helper emits documentation-only plans.  It never executes a setup file,
imports CatMAP, opens a pickle, or launches an external command.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CAPABILITIES_PATH = ROOT / "references" / "software-capability-catalog.json"
RECIPES_PATH = ROOT / "references" / "task-recipes.json"
SOURCES_PATH = ROOT / "references" / "official-sources.yaml"
MAX_JSON_BYTES = 2_000_000


class CatalogError(Exception):
    """A deterministic catalog or request error."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CatalogError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise CatalogError(f"cannot read {path.name}: {exc}") from exc
    if not raw or len(raw) > MAX_JSON_BYTES:
        raise CatalogError(f"{path.name} is empty or exceeds {MAX_JSON_BYTES} bytes")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                CatalogError(f"invalid JSON constant: {token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, CatalogError) as exc:
        raise CatalogError(f"invalid {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise CatalogError(f"{path.name} root must be an object")
    return value


def load_data() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    capabilities = _load_json(CAPABILITIES_PATH)
    recipes = _load_json(RECIPES_PATH)
    sources = _load_json(SOURCES_PATH)
    if (
        capabilities.get("catalog_name") != "catmap-software-capabilities"
        or capabilities.get("schema_version") != "1.0"
    ):
        raise CatalogError("unsupported CatMAP capability catalog identity")
    if (
        recipes.get("catalog_name") != "catmap-task-recipes"
        or recipes.get("schema_version") != "1.0"
    ):
        raise CatalogError("unsupported CatMAP recipe catalog identity")
    if (
        sources.get("catalog_name") != "catmap-official-sources"
        or sources.get("schema_version") != "1.0"
    ):
        raise CatalogError("unsupported CatMAP source catalog identity")
    return capabilities, recipes, sources


def flatten_capabilities(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for kind in ("module", "feature"):
        key = f"{kind}s"
        entries = catalog.get(key)
        if not isinstance(entries, list):
            raise CatalogError(f"capability {key} must be an array")
        for raw in entries:
            if not isinstance(raw, dict):
                raise CatalogError(f"capability {kind} must be an object")
            record_id = raw.get("id")
            group = raw.get("group")
            purpose = raw.get("purpose")
            source_ids = raw.get("source_ids")
            if not isinstance(record_id, str) or not record_id.startswith(f"{kind}."):
                raise CatalogError(f"invalid capability id: {record_id!r}")
            if record_id in records:
                raise CatalogError(f"duplicate capability id: {record_id}")
            if not isinstance(group, str) or not group:
                raise CatalogError(f"capability {record_id} has no group")
            if not isinstance(purpose, str) or not purpose:
                raise CatalogError(f"capability {record_id} has no purpose")
            if not isinstance(source_ids, list) or not source_ids:
                raise CatalogError(f"capability {record_id} has no sources")
            record = dict(raw)
            record["kind"] = kind
            records[record_id] = record
    return records


def flatten_recipes(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = catalog.get("recipes")
    if not isinstance(entries, list):
        raise CatalogError("recipe catalog recipes must be an array")
    records: dict[str, dict[str, Any]] = {}
    states = catalog.get("state_definitions")
    if not isinstance(states, dict) or not states:
        raise CatalogError("recipe state definitions are missing")
    for raw in entries:
        if not isinstance(raw, dict):
            raise CatalogError("recipe must be an object")
        recipe_id = raw.get("id")
        state = raw.get("recipe_state")
        if not isinstance(recipe_id, str) or not recipe_id.startswith("recipe."):
            raise CatalogError(f"invalid recipe id: {recipe_id!r}")
        if recipe_id in records:
            raise CatalogError(f"duplicate recipe id: {recipe_id}")
        if state not in states:
            raise CatalogError(f"recipe {recipe_id} has unknown state: {state!r}")
        for key in (
            "title",
            "surfaces",
            "inputs",
            "calls",
            "outputs",
            "units_and_semantics",
            "scientific_checks",
            "failure_modes",
            "source_ids",
        ):
            value = raw.get(key)
            if key == "title":
                if not isinstance(value, str) or not value:
                    raise CatalogError(f"recipe {recipe_id} has no title")
            elif not isinstance(value, list) or not value:
                raise CatalogError(f"recipe {recipe_id} has invalid {key}")
        records[recipe_id] = dict(raw)
    return records


def validate_source_links(
    capabilities: dict[str, dict[str, Any]],
    recipes: dict[str, dict[str, Any]],
    source_catalog: dict[str, Any],
) -> None:
    raw_sources = source_catalog.get("sources")
    if not isinstance(raw_sources, list):
        raise CatalogError("official sources must be an array")
    source_ids = {
        item.get("id") for item in raw_sources if isinstance(item, dict)
    }
    if None in source_ids or len(source_ids) != len(raw_sources):
        raise CatalogError("official source ids are missing or duplicated")
    for record in [*capabilities.values(), *recipes.values()]:
        unknown = sorted(set(record["source_ids"]) - source_ids)
        if unknown:
            raise CatalogError(f"{record['id']} has unknown source ids: {unknown}")


def groups_report(capabilities: dict[str, dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for record in capabilities.values():
        counts[record["group"]] = counts.get(record["group"], 0) + 1
    return {
        "status": "pass",
        "operation": "groups",
        "groups": [
            {"group": group, "count": count} for group, count in sorted(counts.items())
        ],
        "native_execution_performed": False,
    }


def list_report(
    capabilities: dict[str, dict[str, Any]],
    group: str | None,
    kind: str | None,
) -> dict[str, Any]:
    selected = [
        record
        for _, record in sorted(capabilities.items())
        if (group is None or record["group"] == group)
        and (kind is None or record["kind"] == kind)
    ]
    if group is not None and not selected:
        raise CatalogError(f"unknown or empty capability group: {group}")
    return {
        "status": "pass",
        "operation": "list",
        "group_filter": group,
        "kind_filter": kind,
        "count": len(selected),
        "capabilities": selected,
        "native_execution_performed": False,
    }


def search_report(
    capabilities: dict[str, dict[str, Any]], query: str
) -> dict[str, Any]:
    normalized = " ".join(
        "".join(character if character.isalnum() else " " for character in query.casefold()).split()
    )
    if not normalized:
        raise CatalogError("search query must not be empty")
    matches = []
    for _, record in sorted(capabilities.items()):
        raw_haystack = json.dumps(record, sort_keys=True).casefold()
        haystack = " ".join(
            "".join(
                character if character.isalnum() else " " for character in raw_haystack
            ).split()
        )
        if normalized in haystack:
            matches.append(record)
    return {
        "status": "pass",
        "operation": "search",
        "query": query,
        "count": len(matches),
        "capabilities": matches,
        "native_execution_performed": False,
    }


def show_report(
    capabilities: dict[str, dict[str, Any]], record_id: str
) -> dict[str, Any]:
    try:
        record = capabilities[record_id]
    except KeyError as exc:
        raise CatalogError(f"unknown capability id: {record_id}") from exc
    return {
        "status": "pass",
        "operation": "show",
        "record": record,
        "native_execution_performed": False,
    }


def recipes_report(
    recipes: dict[str, dict[str, Any]], state: str | None
) -> dict[str, Any]:
    selected = [
        record
        for _, record in sorted(recipes.items())
        if state is None or record["recipe_state"] == state
    ]
    if state is not None and not selected:
        raise CatalogError(f"unknown or empty recipe state: {state}")
    return {
        "status": "pass",
        "operation": "recipes",
        "state_filter": state,
        "count": len(selected),
        "recipes": selected,
        "native_execution_performed": False,
    }


def recipe_report(
    recipes: dict[str, dict[str, Any]], recipe_id: str
) -> dict[str, Any]:
    try:
        recipe = recipes[recipe_id]
    except KeyError as exc:
        raise CatalogError(f"unknown recipe id: {recipe_id}") from exc
    return {
        "status": "pass",
        "operation": "recipe",
        "recipe": recipe,
        "native_validation_state": "native-not-run",
        "native_execution_performed": False,
    }


def plan_report(
    recipes: dict[str, dict[str, Any]], recipe_id: str
) -> tuple[dict[str, Any], int]:
    try:
        recipe = recipes[recipe_id]
    except KeyError as exc:
        raise CatalogError(f"unknown recipe id: {recipe_id}") from exc
    report = {
        "operation": "plan",
        "recipe": recipe,
        "native_validation_state": "native-not-run",
        "native_execution_performed": False,
        "execution_authorized": False,
        "trust_boundary": (
            "CatMAP setup/log/Python and pickle artifacts may execute code or deserialize "
            "objects; use only reviewed trusted inputs in an isolated pinned environment."
        ),
        "guard_handoff": "Run catmap_guard.py only on the declarative JSON interchange.",
        "recipe_reference": "references/calling-and-recipes.md",
    }
    if recipe["recipe_state"] == "feature-only":
        report.update(
            {
                "status": "blocked",
                "finding": "CATMAP_FEATURE_ONLY_NO_VALIDATED_RECIPE",
                "minimum_next_action": (
                    "Create a version-matched scientific profile and forward fixture for "
                    "this feature before execution or interpretation."
                ),
            }
        )
        return report, 3
    report.update(
        {
            "status": "documentation-plan",
            "finding": None,
            "minimum_next_action": (
                "Review trusted inputs, pin tag commit and solver branch, run in an isolated "
                "authorized environment, then export declarative evidence for the guard."
            ),
        }
    )
    return report, 0


def _distribution_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def probe_report() -> dict[str, Any]:
    executable = shutil.which("catmap")
    distributions = {
        name: _distribution_version(name) for name in ("python-catmap", "catmap", "CatMAP")
    }
    module_discoverable = importlib.util.find_spec("catmap") is not None
    available = executable is not None or module_discoverable or any(distributions.values())
    return {
        "status": "available-unverified" if available else "unavailable",
        "operation": "probe",
        "executable": executable,
        "distributions": distributions,
        "module_discoverable": module_discoverable,
        "module_imported": False,
        "help_or_version_executed": False,
        "native_execution_performed": False,
        "version_identity_warning": (
            "The v0.4.1 tagged setup.py and catmap.__version__ still report 0.3.1; "
            "metadata alone cannot establish the release tag."
        ),
        "scientific_capability_claim": "none",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    subparsers.add_parser("groups")
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--group")
    list_parser.add_argument("--kind", choices=("module", "feature"))
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    show_parser = subparsers.add_parser("show")
    show_parser.add_argument("record_id")
    recipes_parser = subparsers.add_parser("recipes")
    recipes_parser.add_argument("--state")
    recipe_parser = subparsers.add_parser("recipe")
    recipe_parser.add_argument("recipe_id")
    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("recipe_id")
    subparsers.add_parser("probe")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.operation == "probe":
            report, exit_code = probe_report(), 0
        else:
            catalog, recipe_catalog, sources = load_data()
            capabilities = flatten_capabilities(catalog)
            recipes = flatten_recipes(recipe_catalog)
            validate_source_links(capabilities, recipes, sources)
            if args.operation == "groups":
                report, exit_code = groups_report(capabilities), 0
            elif args.operation == "list":
                report, exit_code = list_report(capabilities, args.group, args.kind), 0
            elif args.operation == "search":
                report, exit_code = search_report(capabilities, args.query), 0
            elif args.operation == "show":
                report, exit_code = show_report(capabilities, args.record_id), 0
            elif args.operation == "recipes":
                report, exit_code = recipes_report(recipes, args.state), 0
            elif args.operation == "recipe":
                report, exit_code = recipe_report(recipes, args.recipe_id), 0
            else:
                report, exit_code = plan_report(recipes, args.recipe_id)
    except CatalogError as exc:
        report = {
            "status": "error",
            "operation": args.operation,
            "error": str(exc),
            "native_execution_performed": False,
        }
        exit_code = 2
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
