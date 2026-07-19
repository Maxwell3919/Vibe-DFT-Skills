#!/usr/bin/env python3
"""Search the official VASPKIT task catalog and emit documentation-only plans.

This helper never launches VASPKIT and never edits a calculation directory.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "references" / "official-task-catalog.json"
RECIPES_PATH = ROOT / "references" / "task-recipes.json"
MAX_JSON_BYTES = 2_000_000


class CatalogError(Exception):
    pass


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
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CatalogError(f"{path.name} is not UTF-8") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                CatalogError(f"invalid JSON constant: {token}")
            ),
        )
    except (json.JSONDecodeError, CatalogError) as exc:
        raise CatalogError(f"invalid {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise CatalogError(f"{path.name} root must be an object")
    return value


def load_data() -> tuple[dict[str, Any], dict[str, Any]]:
    catalog = _load_json(CATALOG_PATH)
    recipes = _load_json(RECIPES_PATH)
    if catalog.get("software") != "VASPKIT" or catalog.get("schema_version") != "1.0":
        raise CatalogError("unsupported task catalog identity")
    if recipes.get("software") != "VASPKIT" or recipes.get("schema_version") != "1.0":
        raise CatalogError("unsupported recipe catalog identity")
    return catalog, recipes


def flatten_tasks(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tasks: dict[str, dict[str, Any]] = {}
    categories = catalog.get("categories")
    if not isinstance(categories, list):
        raise CatalogError("catalog categories must be an array")
    for category in categories:
        if not isinstance(category, dict):
            raise CatalogError("catalog category must be an object")
        category_id = category.get("id")
        category_name = category.get("name")
        entries = category.get("tasks")
        if not isinstance(category_id, str) or not isinstance(category_name, str):
            raise CatalogError("catalog category identity is invalid")
        if not isinstance(entries, dict):
            raise CatalogError(f"category {category_id} tasks must be an object")
        for task_id, purpose in entries.items():
            if not isinstance(task_id, str) or not task_id.isdigit() or len(task_id) != 3:
                raise CatalogError(f"invalid task id: {task_id!r}")
            if task_id in tasks:
                raise CatalogError(f"duplicate task id across categories: {task_id}")
            if not isinstance(purpose, str) or not purpose.strip():
                raise CatalogError(f"task {task_id} has no purpose")
            tasks[task_id] = {
                "task": task_id,
                "purpose": purpose,
                "category": {"id": category_id, "name": category_name},
            }
    expected = catalog.get("statistics", {}).get("feature_page_tasks")
    if not isinstance(expected, int) or len(tasks) != expected:
        raise CatalogError(
            f"catalog task count mismatch: expected {expected!r}, found {len(tasks)}"
        )
    return tasks


def _conflict_matches(task_id: str, expression: str) -> bool:
    if expression == task_id:
        return True
    if "-" not in expression:
        return False
    left, right = expression.split("-", 1)
    if left.isdigit() and right.isdigit():
        return int(left) <= int(task_id) <= int(right)
    return False


def conflicts_for(catalog: dict[str, Any], task_id: str) -> list[dict[str, Any]]:
    conflicts = catalog.get("documentation_conflicts", [])
    if not isinstance(conflicts, list):
        raise CatalogError("documentation_conflicts must be an array")
    return [
        item
        for item in conflicts
        if isinstance(item, dict)
        and isinstance(item.get("task"), str)
        and _conflict_matches(task_id, item["task"])
    ]


def task_record(
    catalog: dict[str, Any],
    recipe_catalog: dict[str, Any],
    task_id: str,
) -> dict[str, Any]:
    tasks = flatten_tasks(catalog)
    if task_id not in tasks:
        supplemental = catalog.get("supplemental_tutorial_tasks", {})
        if task_id in supplemental:
            return {
                "task": task_id,
                "purpose": supplemental[task_id],
                "category": {"id": "71", "name": "Optical properties"},
                "catalog_evidence": "official-tutorial-only",
                "recipe": recipe_catalog.get("recipes", {}).get(task_id),
                "documentation_conflicts": conflicts_for(catalog, task_id),
                "native_validation": catalog.get("native_validation"),
            }
        raise CatalogError(f"unknown VASPKIT task id: {task_id}")
    record = dict(tasks[task_id])
    record.update(
        {
            "catalog_evidence": "official-feature-listed",
            "recipe": recipe_catalog.get("recipes", {}).get(task_id),
            "documentation_conflicts": conflicts_for(catalog, task_id),
            "native_validation": catalog.get("native_validation"),
        }
    )
    return record


def categories_report(catalog: dict[str, Any]) -> dict[str, Any]:
    categories = [
        {
            "id": category["id"],
            "name": category["name"],
            "task_count": len(category["tasks"]),
        }
        for category in catalog["categories"]
    ]
    return {
        "status": "pass",
        "operation": "categories",
        "documentation_series": catalog["documentation_series"],
        "categories": categories,
        "top_level_only_categories": catalog["top_level_only_categories"],
        "native_execution_performed": False,
    }


def list_report(catalog: dict[str, Any], category_id: str | None) -> dict[str, Any]:
    tasks = flatten_tasks(catalog)
    selected = [
        value
        for _, value in sorted(tasks.items())
        if category_id is None or value["category"]["id"] == category_id
    ]
    if category_id is not None and not selected:
        raise CatalogError(f"unknown or empty category: {category_id}")
    return {
        "status": "pass",
        "operation": "list",
        "category_filter": category_id,
        "count": len(selected),
        "tasks": selected,
        "native_execution_performed": False,
    }


def search_report(catalog: dict[str, Any], query: str) -> dict[str, Any]:
    normalized = query.casefold().strip()
    if not normalized:
        raise CatalogError("search query must not be empty")
    tasks = flatten_tasks(catalog)
    matches = []
    for task_id, value in sorted(tasks.items()):
        haystack = " ".join(
            [
                task_id,
                value["purpose"],
                value["category"]["id"],
                value["category"]["name"],
            ]
        ).casefold()
        if normalized in haystack:
            matches.append(value)
    return {
        "status": "pass",
        "operation": "search",
        "query": query,
        "count": len(matches),
        "tasks": matches,
        "native_execution_performed": False,
    }


def show_report(
    catalog: dict[str, Any], recipe_catalog: dict[str, Any], task_id: str
) -> dict[str, Any]:
    return {
        "status": "pass",
        "operation": "show",
        "record": task_record(catalog, recipe_catalog, task_id),
        "native_execution_performed": False,
    }


def plan_report(
    catalog: dict[str, Any], recipe_catalog: dict[str, Any], task_id: str
) -> tuple[dict[str, Any], int]:
    record = task_record(catalog, recipe_catalog, task_id)
    recipe = record.get("recipe")
    conflicts = record["documentation_conflicts"]
    base = {
        "operation": "plan",
        "task": task_id,
        "purpose": record["purpose"],
        "category": record["category"],
        "catalog_evidence": record["catalog_evidence"],
        "recipe": recipe,
        "documentation_conflicts": conflicts,
        "native_validation": record["native_validation"],
        "native_execution_performed": False,
        "execution_authorized": False,
        "recipe_reference": "references/calling-and-recipes.md",
    }
    if conflicts:
        base.update(
            {
                "status": "blocked",
                "finding": "VASPKIT_DOCUMENTATION_CONFLICT",
                "minimum_next_action": (
                    "Inspect and capture the exact installed VASPKIT banner, help, "
                    "menu label, and prompt sequence before automation."
                ),
            }
        )
        return base, 3
    if not isinstance(recipe, dict):
        base.update(
            {
                "status": "blocked",
                "finding": "VASPKIT_RECIPE_NOT_ESTABLISHED",
                "minimum_next_action": (
                    "Use the exact binary interactively, capture prompts and outputs, "
                    "and add a version-specific official/manual-grounded recipe."
                ),
            }
        )
        return base, 3
    if recipe.get("status") == "official-feature-only":
        base.update(
            {
                "status": "blocked",
                "finding": "VASPKIT_FEATURE_LISTING_ONLY",
                "minimum_next_action": recipe["caution"],
            }
        )
        return base, 3
    stdin_template = recipe.get("stdin_template")
    base.update(
        {
            "status": "documentation-plan",
            "finding": None,
            "stdin_file_text": (
                "\n".join(stdin_template) + "\n"
                if isinstance(stdin_template, list)
                else None
            ),
            "minimum_next_action": (
                "Resolve placeholders, verify the exact binary menu and all required "
                "files in a scratch copy, then request explicit native execution."
            ),
        }
    )
    return base, 0


def probe_report() -> dict[str, Any]:
    resolved = shutil.which("vaspkit")
    return {
        "status": "available-unverified" if resolved else "unavailable",
        "operation": "probe",
        "executable_name": "vaspkit",
        "resolved_path": resolved,
        "help_or_banner_executed": False,
        "native_execution_performed": False,
        "scientific_capability_claim": "none",
        "minimum_next_action": (
            "Capture banner, help, executable hash, platform, usage-agreement review, "
            "and a scratch-directory transcript."
            if resolved
            else "Install or explicitly provide a compatible VASPKIT executable before native validation."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Search the pinned official VASPKIT task catalog. "
            "This helper never launches VASPKIT."
        )
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("categories", help="List official task families")
    list_parser = commands.add_parser("list", help="List tasks")
    list_parser.add_argument("--category", help="Two-digit category id")
    search_parser = commands.add_parser("search", help="Search ids and purposes")
    search_parser.add_argument("query")
    show_parser = commands.add_parser("show", help="Show one task and recipe state")
    show_parser.add_argument("task")
    plan_parser = commands.add_parser(
        "plan", help="Emit a documentation-only command/input plan"
    )
    plan_parser.add_argument("task")
    commands.add_parser("probe", help="Resolve vaspkit in PATH without executing it")
    return parser


def _emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "probe":
            _emit(probe_report())
            return 0 if shutil.which("vaspkit") else 3
        catalog, recipes = load_data()
        if args.command == "categories":
            report, exit_code = categories_report(catalog), 0
        elif args.command == "list":
            report, exit_code = list_report(catalog, args.category), 0
        elif args.command == "search":
            report, exit_code = search_report(catalog, args.query), 0
        elif args.command == "show":
            report, exit_code = show_report(catalog, recipes, args.task), 0
        elif args.command == "plan":
            report, exit_code = plan_report(catalog, recipes, args.task)
        else:
            raise CatalogError(f"unsupported command: {args.command}")
        _emit(report)
        return exit_code
    except CatalogError as exc:
        _emit(
            {
                "status": "fail",
                "operation": getattr(args, "command", None),
                "finding": "VASPKIT_CATALOG_INVALID",
                "message": str(exc),
                "native_execution_performed": False,
                "execution_authorized": False,
            }
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
