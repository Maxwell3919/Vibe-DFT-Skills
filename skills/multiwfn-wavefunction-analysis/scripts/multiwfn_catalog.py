#!/usr/bin/env python3
"""Search pinned Multiwfn manual facts and emit non-executing recipe plans.

This helper never launches Multiwfn, never feeds a menu, and never edits an
analysis directory.  Native execution requires a separate, explicitly
authorized adapter after an exact-binary transcript has been validated.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "references" / "official-function-catalog.json"
RECIPES_PATH = ROOT / "references" / "task-recipes.json"
MAX_JSON_BYTES = 2_000_000


class CatalogError(Exception):
    """Raised when pinned catalog data or a catalog request is invalid."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise CatalogError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_constant(token: str) -> None:
    raise CatalogError(f"invalid JSON constant: {token}")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise CatalogError(f"cannot read {path.name}: {exc}") from exc
    if not raw or len(raw) > MAX_JSON_BYTES:
        raise CatalogError(f"{path.name} is empty or exceeds {MAX_JSON_BYTES} bytes")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise CatalogError(f"{path.name} has a forbidden UTF-8 BOM")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, CatalogError) as exc:
        raise CatalogError(f"invalid {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise CatalogError(f"{path.name} root must be an object")
    return value


def load_data() -> tuple[dict[str, Any], dict[str, Any]]:
    catalog = _load_json(CATALOG_PATH)
    recipes = _load_json(RECIPES_PATH)
    for value, label in ((catalog, "function catalog"), (recipes, "recipe catalog")):
        if value.get("schema_version") != "1.0" or value.get("software") != "Multiwfn":
            raise CatalogError(f"unsupported {label} identity")
        if value.get("program_version") != "2026.7.15":
            raise CatalogError(f"unsupported {label} program version")
        if value.get("manual_version") != "2026.7.10":
            raise CatalogError(f"unsupported {label} manual version")
    _function_records(catalog)
    _recipe_records(recipes)
    return catalog, recipes


def _function_records(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    main_functions = catalog.get("main_functions")
    if not isinstance(main_functions, list):
        raise CatalogError("main_functions must be an array")
    records: list[dict[str, Any]] = []
    main_ids: set[str] = set()
    sub_ids: set[str] = set()
    for main in main_functions:
        if not isinstance(main, dict):
            raise CatalogError("main function record must be an object")
        main_id = main.get("id")
        title = main.get("title")
        section = main.get("manual_section")
        subfunctions = main.get("subfunctions")
        if (
            not isinstance(main_id, str)
            or not main_id
            or not isinstance(title, str)
            or not title.strip()
            or not isinstance(section, str)
            or not section
            or not isinstance(subfunctions, list)
        ):
            raise CatalogError("invalid main function identity")
        if main_id in main_ids:
            raise CatalogError(f"duplicate main function id: {main_id}")
        main_ids.add(main_id)
        main_record = {key: value for key, value in main.items() if key != "subfunctions"}
        records.append({"kind": "main-function", **main_record})
        local_ids: set[str] = set()
        for subfunction in subfunctions:
            if not isinstance(subfunction, dict):
                raise CatalogError(f"main function {main_id} has an invalid subfunction")
            sub_id = subfunction.get("id")
            sub_title = subfunction.get("title")
            if (
                not isinstance(sub_id, str)
                or not sub_id
                or not isinstance(sub_title, str)
                or not sub_title.strip()
            ):
                raise CatalogError(f"main function {main_id} has an invalid subfunction identity")
            full_id = f"{main_id}.{sub_id}"
            if sub_id in local_ids or full_id in sub_ids:
                raise CatalogError(f"duplicate subfunction id: {full_id}")
            local_ids.add(sub_id)
            sub_ids.add(full_id)
            records.append(
                {
                    "kind": "subfunction",
                    "id": full_id,
                    "menu_tokens": [main_id, sub_id],
                    "title": sub_title,
                    "main_function": {
                        "id": main_id,
                        "title": title,
                        "manual_section": section,
                    },
                    "evidence": "manual-index-listing-only",
                }
            )
    if len(main_ids) != 29:
        raise CatalogError(f"expected 29 main functions, found {len(main_ids)}")
    return records


def _input_family_records(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    families = catalog.get("input_families")
    if not isinstance(families, list):
        raise CatalogError("input_families must be an array")
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for family in families:
        if not isinstance(family, dict) or not isinstance(family.get("id"), str):
            raise CatalogError("invalid input-family record")
        family_id = family["id"]
        if family_id in seen:
            raise CatalogError(f"duplicate input-family id: {family_id}")
        seen.add(family_id)
        records.append({"kind": "input-family", **family})
    return records


def _recipe_records(recipes: dict[str, Any]) -> list[dict[str, Any]]:
    recipe_map = recipes.get("recipes")
    if not isinstance(recipe_map, dict):
        raise CatalogError("recipes must be an object")
    records: list[dict[str, Any]] = []
    required = {
        "status",
        "mode",
        "argv",
        "stdin_sequence",
        "required_files",
        "expected_outputs",
        "batch_ready",
        "source",
        "checks",
        "caution",
    }
    for recipe_id, recipe in recipe_map.items():
        if not isinstance(recipe_id, str) or not recipe_id or not isinstance(recipe, dict):
            raise CatalogError("invalid recipe record")
        if not required.issubset(recipe):
            missing = ", ".join(sorted(required - set(recipe)))
            raise CatalogError(f"recipe {recipe_id} is missing: {missing}")
        if not isinstance(recipe["argv"], list) or not all(
            isinstance(token, str) for token in recipe["argv"]
        ):
            raise CatalogError(f"recipe {recipe_id} argv must be an array of strings")
        if not isinstance(recipe["stdin_sequence"], list) or not all(
            isinstance(token, str) for token in recipe["stdin_sequence"]
        ):
            raise CatalogError(f"recipe {recipe_id} stdin_sequence must be an array of strings")
        records.append({"kind": "recipe", "id": recipe_id, **recipe})
    return records


def _records(catalog: dict[str, Any], recipes: dict[str, Any]) -> list[dict[str, Any]]:
    return (
        _function_records(catalog)
        + _input_family_records(catalog)
        + _recipe_records(recipes)
    )


def _normalize(text: str) -> str:
    return " ".join(
        text.casefold()
        .replace("_", " ")
        .replace("-", " ")
        .replace("/", " ")
        .split()
    )


def families_report(catalog: dict[str, Any], recipes: dict[str, Any]) -> dict[str, Any]:
    functions = _function_records(catalog)
    main = [record for record in functions if record["kind"] == "main-function"]
    sub = [record for record in functions if record["kind"] == "subfunction"]
    input_families = _input_family_records(catalog)
    return {
        "status": "pass",
        "operation": "families",
        "program_version": catalog["program_version"],
        "manual_version": catalog["manual_version"],
        "main_function_count": len(main),
        "indexed_subfunction_count": len(sub),
        "input_family_count": len(input_families),
        "recipe_count": len(_recipe_records(recipes)),
        "main_functions": main,
        "input_families": input_families,
        "native_execution_performed": False,
    }


def list_report(
    catalog: dict[str, Any], recipes: dict[str, Any], main_only: bool
) -> dict[str, Any]:
    records = _records(catalog, recipes)
    if main_only:
        records = [record for record in records if record["kind"] == "main-function"]
    return {
        "status": "pass",
        "operation": "list",
        "main_only": main_only,
        "count": len(records),
        "records": records,
        "native_execution_performed": False,
    }


def search_report(
    catalog: dict[str, Any], recipes: dict[str, Any], query: str
) -> dict[str, Any]:
    needle = _normalize(query)
    if not needle:
        raise CatalogError("search query must not be empty")
    matches = []
    for record in _records(catalog, recipes):
        haystack = _normalize(json.dumps(record, ensure_ascii=False, sort_keys=True))
        if needle in haystack:
            matches.append(record)
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
        record
        for record in _records(catalog, recipes)
        if record["id"].casefold() == record_id.casefold()
    ]
    if not matches:
        raise CatalogError(f"unknown catalog id: {record_id}")
    if len(matches) > 1:
        kinds = ", ".join(record["kind"] for record in matches)
        raise CatalogError(f"ambiguous catalog id {record_id}: {kinds}")
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
        "program_version": catalog["program_version"],
        "manual_version": catalog["manual_version"],
        "native_validation": catalog["native_validation"],
        "execution_authorized": False,
        "native_execution_performed": False,
        "recipe_reference": "references/calling-and-recipes.md",
    }
    if recipe_id not in recipe_map:
        base.update(
            {
                "status": "blocked",
                "finding": "MULTIWFN_RECIPE_NOT_ESTABLISHED",
                "message": (
                    "A function-family or submenu listing is not an exact, "
                    "version-safe stdin recipe."
                ),
                "minimum_next_action": (
                    "Capture the exact installed banner, complete prompt transcript, "
                    "stdin, output identities, and failure behavior before adding a recipe."
                ),
            }
        )
        return base, 3
    recipe = recipe_map[recipe_id]
    base.update(
        {
            "status": "documentation-plan",
            "finding": None,
            "evidence_status": recipe["status"],
            "mode": recipe["mode"],
            "argv": recipe["argv"],
            "stdin_sequence": recipe["stdin_sequence"],
            "stdin_file_text": "\n".join(recipe["stdin_sequence"]) + "\n",
            "required_files": recipe["required_files"],
            "expected_outputs": recipe["expected_outputs"],
            "batch_ready_in_manual": recipe["batch_ready"],
            "checks": recipe["checks"],
            "caution": recipe["caution"],
            "source": recipe["source"],
            "minimum_next_action": (
                "Resolve placeholders in a fresh scratch directory and verify the exact "
                "binary/menu transcript; request native execution separately."
            ),
        }
    )
    return base, 0


def probe_report() -> dict[str, Any]:
    resolved = {name: shutil.which(name) for name in ("Multiwfn", "multiwfn")}
    try:
        distribution_version: str | None = importlib.metadata.version("multiwfn")
    except importlib.metadata.PackageNotFoundError:
        distribution_version = None
    available = any(resolved.values()) or distribution_version is not None
    return {
        "status": "available-unverified" if available else "tool-unavailable",
        "operation": "probe",
        "executables": resolved,
        "python_distribution_version": distribution_version,
        "banner_or_help_executed": False,
        "native_execution_performed": False,
        "scientific_capability_claim": "none",
        "minimum_next_action": (
            "Record the exact program banner/update date, executable hash, platform, "
            "distribution terms, settings.ini, and one complete private transcript."
        ),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    subparsers.add_parser("families")
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--main", action="store_true")
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
            report, exit_code = probe_report(), 0
        else:
            catalog, recipes = load_data()
            if args.operation == "families":
                report, exit_code = families_report(catalog, recipes), 0
            elif args.operation == "list":
                report, exit_code = list_report(catalog, recipes, args.main), 0
            elif args.operation == "search":
                report, exit_code = search_report(catalog, recipes, args.query), 0
            elif args.operation == "show":
                report, exit_code = show_report(catalog, recipes, args.record_id), 0
            else:
                report, exit_code = plan_report(catalog, recipes, args.recipe_id)
    except CatalogError as exc:
        report, exit_code = {
            "status": "error",
            "finding": "MULTIWFN_CATALOG_ERROR",
            "message": str(exc),
            "native_execution_performed": False,
        }, 2
    json.dump(report, sys.stdout, ensure_ascii=False, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
