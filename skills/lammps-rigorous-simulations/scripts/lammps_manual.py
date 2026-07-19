#!/usr/bin/env python3
"""Read-only LAMMPS 4Jul2026 command/recipe resolver and safe native probe."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "references"
CATALOG_PATH = REFERENCES / "official-command-catalog.json"
RECIPES_PATH = REFERENCES / "task-recipes.json"
FORMATS_PATH = REFERENCES / "core-file-formats.json"
NATIVE_PATH = REFERENCES / "native-capability.json"
EXPECTED_VERSION = "4Jul2026"
EXPECTED_BANNER = "LAMMPS (4 Jul 2026)"
MAX_PROVIDER_OUTPUT = 8 * 1024 * 1024
RECIPE_KEYS = {
    "title", "category", "catalog_state", "recipe_state", "native_state",
    "argv_templates", "input_script_template", "required_inputs",
    "expected_outputs", "prerequisites", "restart_checkpoint", "version_notes",
    "failure_modes", "scientific_checks", "sources",
}
EXECUTABLE_TOKENS = {
    "<lammps-executable>", "<same-lammps-executable>",
    "<producing-lammps-executable>", "<lammps-executable-with-COLVARS>",
}


class ManualError(RuntimeError):
    """A stable, user-actionable manual resolver failure."""

    def __init__(self, code: str, message: str, *, incomplete: bool = False):
        super().__init__(message)
        self.code = code
        self.message = message
        self.incomplete = incomplete


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicates)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ManualError("LAMMPS.MANUAL.INVALID_JSON", f"Invalid catalog JSON: {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise ManualError("LAMMPS.MANUAL.INVALID_SHAPE", f"Catalog root must be an object: {path.name}")
    return value


def _official_url(url: Any) -> bool:
    return isinstance(url, str) and (
        url.startswith("https://docs.lammps.org/")
        or url.startswith("https://github.com/lammps/lammps/")
        or url.startswith("https://raw.githubusercontent.com/lammps/lammps/patch_4Jul2026/")
    )


def validate_catalogs() -> dict[str, Any]:
    catalog = load_json(CATALOG_PATH)
    recipes = load_json(RECIPES_PATH)
    formats = load_json(FORMATS_PATH)
    native = load_json(NATIVE_PATH)
    pinned = catalog.get("pinned_release")
    if catalog.get("software") != "LAMMPS" or not isinstance(pinned, dict) or pinned.get("version") != EXPECTED_VERSION or pinned.get("banner") != EXPECTED_BANNER:
        raise ManualError("LAMMPS.MANUAL.VERSION", "Command catalog is not pinned to LAMMPS 4Jul2026.")
    indexes = catalog.get("complete_indexes")
    general = catalog.get("general_commands")
    high_use = catalog.get("high_use_records")
    if not isinstance(indexes, list) or len(indexes) != 10 or not isinstance(general, list) or len(general) < 100 or not isinstance(high_use, list) or len(high_use) < 30:
        raise ManualError("LAMMPS.MANUAL.INVALID_SHAPE", "Command catalog coverage is incomplete.")
    if len(general) != len(set(general)):
        raise ManualError("LAMMPS.MANUAL.DUPLICATE", "General command catalog contains duplicate names.")
    for index in indexes:
        if not isinstance(index, dict) or not _official_url(index.get("online_url")) or not _official_url(index.get("pinned_source_url")):
            raise ManualError("LAMMPS.MANUAL.SOURCE", "A command-family index lacks official pinned evidence.")
    recipe_map = recipes.get("recipes")
    if recipes.get("software") != "LAMMPS" or recipes.get("pinned_version") != EXPECTED_VERSION or not isinstance(recipe_map, dict):
        raise ManualError("LAMMPS.MANUAL.VERSION", "Recipe catalog is not pinned to LAMMPS 4Jul2026.")
    for record in high_use:
        if not isinstance(record, dict) or not isinstance(record.get("name"), str) or not _official_url(record.get("manual_url")):
            raise ManualError("LAMMPS.MANUAL.INVALID_SHAPE", "A high-use command record is malformed.")
        if any(recipe_id not in recipe_map for recipe_id in record.get("recipe_ids", [])):
            raise ManualError("LAMMPS.MANUAL.RECIPE_LINK", f"Command has an unresolved recipe link: {record['name']}")
    for recipe_id, recipe in recipe_map.items():
        if not isinstance(recipe_id, str) or not recipe_id or not isinstance(recipe, dict) or set(recipe) != RECIPE_KEYS:
            raise ManualError("LAMMPS.MANUAL.INVALID_SHAPE", f"Recipe has a noncanonical shape: {recipe_id}")
        if recipe["native_state"] not in {"not-run", "native-not-run", "native-validated"}:
            raise ManualError("LAMMPS.MANUAL.STATE", f"Recipe native state is invalid: {recipe_id}")
        argv_templates = recipe["argv_templates"]
        if not isinstance(argv_templates, list) or not argv_templates:
            raise ManualError("LAMMPS.MANUAL.INVALID_ARGV", f"Recipe has no argv sequence: {recipe_id}")
        for argv in argv_templates:
            if not isinstance(argv, list) or not argv or not all(isinstance(token, str) and token for token in argv):
                raise ManualError("LAMMPS.MANUAL.INVALID_ARGV", f"Recipe argv is not an explicit token array: {recipe_id}")
        if not isinstance(recipe["sources"], list) or not recipe["sources"] or not all(_official_url(url) for url in recipe["sources"]):
            raise ManualError("LAMMPS.MANUAL.SOURCE", f"Recipe lacks official sources: {recipe_id}")
    format_records = formats.get("formats")
    if formats.get("software") != "LAMMPS" or formats.get("pinned_version") != EXPECTED_VERSION or not isinstance(format_records, list) or len(format_records) < 8:
        raise ManualError("LAMMPS.MANUAL.FORMATS", "Core file-format catalog is incomplete.")
    if native.get("software") != "LAMMPS" or native.get("expected_version") != EXPECTED_VERSION or native.get("expected_banner") != EXPECTED_BANNER or native.get("state") not in {"native-not-run", "native-validated"}:
        raise ManualError("LAMMPS.MANUAL.NATIVE", "Native capability record is malformed.")
    return {
        "status": "valid",
        "software": "LAMMPS",
        "pinned_version": EXPECTED_VERSION,
        "general_command_count": len(general),
        "high_use_record_count": len(high_use),
        "recipe_count": len(recipe_map),
        "format_count": len(format_records),
        "native_state": native["state"],
    }


def _search_blob(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).casefold()


def list_commands(query: str | None, category: str | None) -> dict[str, Any]:
    validate_catalogs()
    catalog = load_json(CATALOG_PATH)
    selected = [
        record for record in catalog["high_use_records"]
        if (category is None or record["category"] == category)
        and (query is None or query.casefold() in _search_blob(record))
    ]
    general_matches = [
        name for name in catalog["general_commands"]
        if query is not None and query.casefold() in name.casefold()
    ]
    return {
        "software": "LAMMPS",
        "pinned_version": EXPECTED_VERSION,
        "high_use_count": len(selected),
        "high_use_records": selected,
        "general_name_matches": general_matches,
        "complete_style_indexes": catalog["complete_indexes"],
    }


def list_recipes(query: str | None, category: str | None) -> dict[str, Any]:
    validate_catalogs()
    recipes = load_json(RECIPES_PATH)["recipes"]
    selected = [
        {"recipe_id": recipe_id, **recipe}
        for recipe_id, recipe in recipes.items()
        if (category is None or recipe["category"] == category)
        and (query is None or query.casefold() in _search_blob({"recipe_id": recipe_id, **recipe}))
    ]
    return {"software": "LAMMPS", "pinned_version": EXPECTED_VERSION, "count": len(selected), "recipes": selected}


def _render_executable(value: Any, executable: str) -> Any:
    if isinstance(value, str):
        return executable if value in EXECUTABLE_TOKENS else value
    if isinstance(value, list):
        return [_render_executable(item, executable) for item in value]
    if isinstance(value, dict):
        return {key: _render_executable(item, executable) for key, item in value.items()}
    return value


def _placeholders(value: Any) -> list[str]:
    return sorted(set(re.findall(r"<[^<>]+>", json.dumps(value, ensure_ascii=False))))


def show_recipe(recipe_id: str, executable: str, require_ready: bool) -> dict[str, Any]:
    validate_catalogs()
    recipe = load_json(RECIPES_PATH)["recipes"].get(recipe_id)
    if recipe is None:
        raise ManualError("LAMMPS.MANUAL.RECIPE_NOT_FOUND", f"No official recipe is registered for {recipe_id}.", incomplete=True)
    rendered = _render_executable(recipe, executable)
    unresolved = _placeholders(rendered)
    if require_ready and unresolved:
        raise ManualError(
            "LAMMPS.MANUAL.UNRESOLVED_PARAMETERS",
            "Recipe is manual-grounded but not runnable until these parameters are resolved: " + ", ".join(unresolved),
            incomplete=True,
        )
    return {
        "software": "LAMMPS",
        "pinned_version": EXPECTED_VERSION,
        "recipe_id": recipe_id,
        "rendered_executable_label": Path(executable).name,
        "unresolved_parameters": unresolved,
        "recipe": rendered,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_executable(value: str) -> Path | None:
    candidate = Path(value).expanduser()
    resolved_value = str(candidate) if candidate.is_absolute() or os.sep in value else shutil.which(value)
    if resolved_value is None:
        return None
    resolved = Path(resolved_value).resolve()
    try:
        metadata = resolved.stat()
    except OSError:
        return None
    if not stat.S_ISREG(metadata.st_mode) or not os.access(resolved, os.X_OK):
        return None
    return resolved


def _run_help(executable: Path, cwd: str) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["LC_ALL"] = "C"
    try:
        completed = subprocess.run(
            [str(executable), "-help"], cwd=cwd, env=environment,
            check=False, capture_output=True, timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ManualError("LAMMPS.NATIVE.PROBE_FAILED", f"Safe provider probe failed: {type(exc).__name__}", incomplete=True) from exc
    output = completed.stdout + b"\n" + completed.stderr
    if len(output) > MAX_PROVIDER_OUTPUT:
        raise ManualError("LAMMPS.NATIVE.OUTPUT_LIMIT", "Provider help output exceeded 8 MiB.", incomplete=True)
    return {
        "argv": [executable.name, "-help"],
        "returncode": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
        "stdout_bytes": len(completed.stdout),
        "stderr_bytes": len(completed.stderr),
        "combined_text": output.decode("utf-8", errors="replace"),
    }


def probe_native(executable_name: str, required_styles: list[str]) -> tuple[int, dict[str, Any]]:
    validate_catalogs()
    executable = _resolve_executable(executable_name)
    if executable is None:
        return 3, {
            "probe_contract": "lammps-native-probe@1.0",
            "state": "native-not-run",
            "expected_version": EXPECTED_VERSION,
            "expected_banner": EXPECTED_BANNER,
            "executable_label": Path(executable_name).name,
            "reason": "Executable was not found as an executable regular file.",
        }
    with tempfile.TemporaryDirectory(prefix="lammps-safe-probe-") as directory:
        probe = _run_help(executable, directory)
    text = probe.pop("combined_text")
    banner_matches = re.findall(r"LAMMPS \([^\r\n]+\)", text)
    parsed_banner = banner_matches[0] if banner_matches else None
    style_presence = {style: style in text for style in required_styles}
    passed = probe["returncode"] == 0 and parsed_banner == EXPECTED_BANNER and all(style_presence.values())
    result = {
        "probe_contract": "lammps-native-probe@1.0",
        "state": "native-validated" if passed else "native-probe-failed",
        "expected_version": EXPECTED_VERSION,
        "expected_banner": EXPECTED_BANNER,
        "parsed_banner": parsed_banner,
        "banner_match": parsed_banner == EXPECTED_BANNER,
        "executable_label": executable.name,
        "executable_sha256": _sha256(executable),
        "required_style_presence": style_presence,
        "probe": probe,
        "claim_boundary": "-help success proves only this executable's release/build help and requested style strings; no simulation was run.",
    }
    return (0 if passed else 3), result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="validate bundled command, recipe, format, and native records")
    commands = sub.add_parser("commands", help="search high-use records and the pinned general-command index")
    commands.add_argument("--query")
    commands.add_argument("--category")
    recipes = sub.add_parser("recipes", help="search official-manual task recipes")
    recipes.add_argument("--query")
    recipes.add_argument("--category")
    show = sub.add_parser("show-recipe", help="render one recipe without executing it")
    show.add_argument("recipe_id")
    show.add_argument("--executable", default="lmp")
    show.add_argument("--require-ready", action="store_true")
    probe = sub.add_parser("probe-native", help="run only the fixed -help probe against a selected executable")
    probe.add_argument("--executable", default="lmp")
    probe.add_argument("--require-style", action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        code = 0
        if args.command == "validate":
            result = validate_catalogs()
        elif args.command == "commands":
            result = list_commands(args.query, args.category)
        elif args.command == "recipes":
            result = list_recipes(args.query, args.category)
        elif args.command == "show-recipe":
            result = show_recipe(args.recipe_id, args.executable, args.require_ready)
        else:
            code, result = probe_native(args.executable, args.require_style)
    except ManualError as exc:
        code = 3 if exc.incomplete else 2
        result = {"status": "incomplete" if exc.incomplete else "blocked", "code": exc.code, "message": exc.message}
    except Exception:
        code = 4
        result = {"status": "internal-error", "code": "LAMMPS.MANUAL.INTERNAL", "message": "Unexpected manual resolver failure."}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
