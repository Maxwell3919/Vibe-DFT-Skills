#!/usr/bin/env python3
"""Search the public LOBSTER 5.1.1 evidence catalog without running LOBSTER.

The public provider pages do not publish the complete native command or input
grammar.  This helper therefore fails closed for native execution plans unless
the recipe is a local guard, a companion postprocessor, or a local handoff.
"""

from __future__ import annotations

import argparse
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
CANDIDATE_EXECUTABLES = ("lobster", "lobster-5.1.1", "lobster-5.1.0")


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
        capabilities.get("catalog_name") != "lobster-software-capabilities"
        or capabilities.get("schema_version") != "1.0"
    ):
        raise CatalogError("unsupported LOBSTER capability catalog identity")
    if (
        recipes.get("catalog_name") != "lobster-task-recipes"
        or recipes.get("schema_version") != "1.0"
    ):
        raise CatalogError("unsupported LOBSTER recipe catalog identity")
    if (
        sources.get("catalog_name") != "lobster-official-sources"
        or sources.get("schema_version") != "1.0"
    ):
        raise CatalogError("unsupported LOBSTER source catalog identity")
    return capabilities, recipes, sources


def flatten_capabilities(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = catalog.get("capabilities")
    if not isinstance(entries, list):
        raise CatalogError("capabilities must be an array")
    records: dict[str, dict[str, Any]] = {}
    for raw in entries:
        if not isinstance(raw, dict):
            raise CatalogError("capability must be an object")
        record_id = raw.get("id")
        if not isinstance(record_id, str) or not record_id:
            raise CatalogError(f"invalid capability id: {record_id!r}")
        if record_id in records:
            raise CatalogError(f"duplicate capability id: {record_id}")
        for key in ("group", "surface", "evidence_state", "purpose"):
            if not isinstance(raw.get(key), str) or not raw[key]:
                raise CatalogError(f"capability {record_id} has invalid {key}")
        if not isinstance(raw.get("source_ids"), list) or not raw["source_ids"]:
            raise CatalogError(f"capability {record_id} has no sources")
        records[record_id] = dict(raw)
    return records


def flatten_recipes(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = catalog.get("recipes")
    states = catalog.get("state_definitions")
    if not isinstance(entries, list):
        raise CatalogError("recipes must be an array")
    if not isinstance(states, dict) or not states:
        raise CatalogError("recipe state definitions are missing")
    records: dict[str, dict[str, Any]] = {}
    list_fields = (
        "surfaces",
        "inputs",
        "calls",
        "outputs",
        "units_and_semantics",
        "scientific_checks",
        "failure_modes",
        "source_ids",
    )
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
        if not isinstance(raw.get("title"), str) or not raw["title"]:
            raise CatalogError(f"recipe {recipe_id} has no title")
        for key in list_fields:
            value = raw.get(key)
            if not isinstance(value, list):
                raise CatalogError(f"recipe {recipe_id} has invalid {key}")
            if key != "calls" and not value:
                raise CatalogError(f"recipe {recipe_id} has empty {key}")
        if state in {"manual-required", "design-only"} and raw["calls"]:
            raise CatalogError(
                f"blocked native recipe {recipe_id} must not invent an executable call"
            )
        if state in {"repository-guard", "companion-official-recipe"} and not raw["calls"]:
            raise CatalogError(f"documented callable recipe {recipe_id} has no call")
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
    state: str | None,
) -> dict[str, Any]:
    selected = [
        record
        for _, record in sorted(capabilities.items())
        if (group is None or record["group"] == group)
        and (state is None or record["evidence_state"] == state)
    ]
    if group is not None and not selected:
        raise CatalogError(f"unknown or empty capability group: {group}")
    if state is not None and not selected:
        raise CatalogError(f"unknown or empty evidence state: {state}")
    return {
        "status": "pass",
        "operation": "list",
        "group_filter": group,
        "state_filter": state,
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
    state = recipe["recipe_state"]
    report = {
        "operation": "plan",
        "recipe": recipe,
        "native_validation_state": "native-not-run",
        "native_execution_performed": False,
        "execution_authorized": False,
        "recipe_reference": "references/calling-and-recipes.md",
        "claim_ceiling": "no_positive_claim",
    }
    if state == "manual-required":
        report.update(
            {
                "status": "blocked",
                "finding": "LOBSTER_AUTHORIZED_MANUAL_REQUIRED",
                "minimum_next_action": (
                    "Provide privacy-safe identity evidence for the authorized exact 5.1.1 "
                    "manual/example and binary; review the provider-specific syntax privately."
                ),
            }
        )
        return report, 3
    if state == "design-only":
        report.update(
            {
                "status": "blocked",
                "finding": "LOBSTER_PROVIDER_ROUTE_DESIGN_ONLY",
                "minimum_next_action": (
                    "Create a provider/version-specific parent contract and lawful genuine "
                    "forward fixture before execution."
                ),
            }
        )
        return report, 3
    report.update(
        {
            "status": "documentation-plan",
            "finding": None,
            "minimum_next_action": (
                "Review inputs and upstream gates; execute only the named local or companion "
                "tool in its separately verified environment."
            ),
        }
    )
    return report, 0


def probe_report() -> dict[str, Any]:
    candidates = {name: shutil.which(name) for name in CANDIDATE_EXECUTABLES}
    found = {name: path for name, path in candidates.items() if path is not None}
    return {
        "status": "available-unverified" if found else "unavailable",
        "operation": "probe",
        "candidate_executables": candidates,
        "found_candidates": found,
        "executable_name_authoritative": False,
        "help_or_version_executed": False,
        "native_execution_performed": False,
        "authorization_established": False,
        "provider_version_established": False,
        "scientific_capability_claim": "none",
        "minimum_next_action": (
            "Use the authorized exact 5.1.1 manual and entitlement receipt to identify and "
            "verify the real binary privately; PATH discovery alone is insufficient."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    subparsers.add_parser("groups")
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--group")
    list_parser.add_argument("--state")
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
                report, exit_code = list_report(capabilities, args.group, args.state), 0
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
