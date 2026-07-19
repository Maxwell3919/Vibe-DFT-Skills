#!/usr/bin/env python3
"""Read-only GROMACS 2026.3 command/recipe resolver and safe native probe."""

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
EXPECTED_VERSION = "2026.3"
MAX_PROVIDER_OUTPUT = 4 * 1024 * 1024
RECIPE_KEYS = {
    "title", "category", "catalog_state", "recipe_state", "native_state",
    "argv_templates", "unresolved_parameters", "required_inputs",
    "expected_outputs", "restart_checkpoint", "exit_and_log_semantics",
    "failure_modes", "scientific_checks", "sources",
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
        raise ManualError("GROMACS.MANUAL.INVALID_JSON", f"Invalid catalog JSON: {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise ManualError("GROMACS.MANUAL.INVALID_SHAPE", f"Catalog root must be an object: {path.name}")
    return value


def _official_url(url: Any) -> bool:
    return isinstance(url, str) and (
        url.startswith("https://manual.gromacs.org/documentation/2026.3/")
        or url.startswith("https://ftp.gromacs.org/")
    )


def validate_catalogs() -> dict[str, Any]:
    catalog = load_json(CATALOG_PATH)
    recipes = load_json(RECIPES_PATH)
    formats = load_json(FORMATS_PATH)
    native = load_json(NATIVE_PATH)
    if catalog.get("software") != "GROMACS" or catalog.get("pinned_version") != EXPECTED_VERSION:
        raise ManualError("GROMACS.MANUAL.VERSION", "Command catalog is not pinned to GROMACS 2026.3.")
    commands = catalog.get("commands")
    if not isinstance(commands, list) or not commands:
        raise ManualError("GROMACS.MANUAL.INVALID_SHAPE", "Command catalog is empty or malformed.")
    names: set[str] = set()
    recipe_map = recipes.get("recipes")
    if recipes.get("software") != "GROMACS" or recipes.get("pinned_version") != EXPECTED_VERSION or not isinstance(recipe_map, dict):
        raise ManualError("GROMACS.MANUAL.VERSION", "Recipe catalog is not pinned to GROMACS 2026.3.")
    for command in commands:
        if not isinstance(command, dict) or set(command) != {"name", "category", "catalog_state", "recipe_ids", "manual_url"}:
            raise ManualError("GROMACS.MANUAL.INVALID_SHAPE", "A command record has a noncanonical shape.")
        name = command["name"]
        if not isinstance(name, str) or not name or name in names:
            raise ManualError("GROMACS.MANUAL.DUPLICATE", "Command names must be unique nonempty strings.")
        names.add(name)
        if command["catalog_state"] not in {"official-index-listed", "official-manual-recipe"} or not _official_url(command["manual_url"]):
            raise ManualError("GROMACS.MANUAL.SOURCE", f"Command source/state is not exact-version official evidence: {name}")
        if not isinstance(command["recipe_ids"], list) or any(item not in recipe_map for item in command["recipe_ids"]):
            raise ManualError("GROMACS.MANUAL.RECIPE_LINK", f"Command has an unresolved recipe link: {name}")
    for recipe_id, recipe in recipe_map.items():
        if not isinstance(recipe_id, str) or not recipe_id or not isinstance(recipe, dict):
            raise ManualError("GROMACS.MANUAL.INVALID_SHAPE", "Recipe IDs and bodies must be nonempty objects.")
        allowed = RECIPE_KEYS | {"stdin_lines"}
        if not RECIPE_KEYS.issubset(recipe) or not set(recipe).issubset(allowed):
            raise ManualError("GROMACS.MANUAL.INVALID_SHAPE", f"Recipe has a noncanonical shape: {recipe_id}")
        if recipe["native_state"] not in {"native-not-run", "native-validated"}:
            raise ManualError("GROMACS.MANUAL.STATE", f"Recipe native state is invalid: {recipe_id}")
        if not isinstance(recipe["argv_templates"], list) or not recipe["argv_templates"]:
            raise ManualError("GROMACS.MANUAL.INVALID_SHAPE", f"Recipe has no argv sequence: {recipe_id}")
        for argv in recipe["argv_templates"]:
            if not isinstance(argv, list) or not argv or not all(isinstance(token, str) and token for token in argv):
                raise ManualError("GROMACS.MANUAL.INVALID_ARGV", f"Recipe argv is not an explicit token array: {recipe_id}")
        if not isinstance(recipe["sources"], list) or not recipe["sources"] or not all(_official_url(url) for url in recipe["sources"]):
            raise ManualError("GROMACS.MANUAL.SOURCE", f"Recipe lacks exact-version official sources: {recipe_id}")
    format_records = formats.get("formats")
    if formats.get("software") != "GROMACS" or formats.get("pinned_version") != EXPECTED_VERSION or not isinstance(format_records, list) or len(format_records) < 10:
        raise ManualError("GROMACS.MANUAL.FORMATS", "Core file-format catalog is incomplete.")
    if native.get("software") != "GROMACS" or native.get("expected_version") != EXPECTED_VERSION or native.get("state") not in {"native-not-run", "native-validated"}:
        raise ManualError("GROMACS.MANUAL.NATIVE", "Native capability record is malformed.")
    return {
        "status": "valid",
        "software": "GROMACS",
        "pinned_version": EXPECTED_VERSION,
        "command_count": len(commands),
        "recipe_count": len(recipe_map),
        "format_count": len(format_records),
        "native_state": native["state"],
    }


def _search_blob(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).casefold()


def list_commands(query: str | None, category: str | None) -> dict[str, Any]:
    validate_catalogs()
    commands = load_json(CATALOG_PATH)["commands"]
    selected = [
        item for item in commands
        if (category is None or item["category"] == category)
        and (query is None or query.casefold() in _search_blob(item))
    ]
    return {"software": "GROMACS", "pinned_version": EXPECTED_VERSION, "count": len(selected), "commands": selected}


def list_recipes(query: str | None, category: str | None) -> dict[str, Any]:
    validate_catalogs()
    recipes = load_json(RECIPES_PATH)["recipes"]
    selected = [
        {"recipe_id": recipe_id, **recipe}
        for recipe_id, recipe in recipes.items()
        if (category is None or recipe["category"] == category)
        and (query is None or query.casefold() in _search_blob({"recipe_id": recipe_id, **recipe}))
    ]
    return {"software": "GROMACS", "pinned_version": EXPECTED_VERSION, "count": len(selected), "recipes": selected}


def show_recipe(recipe_id: str, require_ready: bool) -> dict[str, Any]:
    validate_catalogs()
    recipe = load_json(RECIPES_PATH)["recipes"].get(recipe_id)
    if recipe is None:
        raise ManualError("GROMACS.MANUAL.RECIPE_NOT_FOUND", f"No official recipe is registered for {recipe_id}.", incomplete=True)
    unresolved = recipe["unresolved_parameters"]
    if require_ready and unresolved:
        raise ManualError(
            "GROMACS.MANUAL.UNRESOLVED_PARAMETERS",
            "Recipe is manual-grounded but not runnable until these parameters are resolved: " + ", ".join(unresolved),
            incomplete=True,
        )
    return {"software": "GROMACS", "pinned_version": EXPECTED_VERSION, "recipe_id": recipe_id, "recipe": recipe}


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


def _run_probe(executable: Path, argv_tail: list[str], cwd: str) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["LC_ALL"] = "C"
    try:
        completed = subprocess.run(
            [str(executable), *argv_tail], cwd=cwd, env=environment,
            check=False, capture_output=True, timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ManualError("GROMACS.NATIVE.PROBE_FAILED", f"Safe provider probe failed: {type(exc).__name__}", incomplete=True) from exc
    stdout = completed.stdout
    stderr = completed.stderr
    if len(stdout) + len(stderr) > MAX_PROVIDER_OUTPUT:
        raise ManualError("GROMACS.NATIVE.OUTPUT_LIMIT", "Provider probe output exceeded 4 MiB.", incomplete=True)
    return {
        "argv": [executable.name, *argv_tail],
        "returncode": completed.returncode,
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        "stdout_bytes": len(stdout),
        "stderr_bytes": len(stderr),
        "combined_text": (stdout + b"\n" + stderr).decode("utf-8", errors="replace"),
    }


def probe_native(executable_name: str) -> tuple[int, dict[str, Any]]:
    validate_catalogs()
    executable = _resolve_executable(executable_name)
    if executable is None:
        return 3, {
            "probe_contract": "gromacs-native-probe@1.0",
            "state": "native-not-run",
            "expected_version": EXPECTED_VERSION,
            "executable_label": Path(executable_name).name,
            "reason": "Executable was not found as an executable regular file.",
        }
    with tempfile.TemporaryDirectory(prefix="gromacs-safe-probe-") as directory:
        version_probe = _run_probe(executable, ["--version"], directory)
        help_probe = _run_probe(executable, ["help", "commands"], directory)
    combined = version_probe.pop("combined_text") + "\n" + help_probe.pop("combined_text")
    match = re.search(r"(?:GROMACS\s+version\s*:|version)\s*([0-9][A-Za-z0-9._+-]*)", combined, flags=re.IGNORECASE)
    parsed_version = match.group(1) if match else None
    required_tokens = {token: bool(re.search(rf"\b{re.escape(token)}\b", combined)) for token in ("grompp", "mdrun", "check", "energy")}
    passed = (
        version_probe["returncode"] == 0
        and help_probe["returncode"] == 0
        and parsed_version == EXPECTED_VERSION
        and all(required_tokens.values())
    )
    result = {
        "probe_contract": "gromacs-native-probe@1.0",
        "state": "native-validated" if passed else "native-probe-failed",
        "expected_version": EXPECTED_VERSION,
        "parsed_version": parsed_version,
        "version_match": parsed_version == EXPECTED_VERSION,
        "executable_label": executable.name,
        "executable_sha256": _sha256(executable),
        "required_help_tokens": required_tokens,
        "probes": [version_probe, help_probe],
        "claim_boundary": "Version/help success proves only this executable's identity and command surface; no simulation was run.",
    }
    return (0 if passed else 3), result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="validate bundled command, recipe, format, and native records")
    commands = sub.add_parser("commands", help="search the high-use official command catalog")
    commands.add_argument("--query")
    commands.add_argument("--category")
    recipes = sub.add_parser("recipes", help="search official-manual task recipes")
    recipes.add_argument("--query")
    recipes.add_argument("--category")
    show = sub.add_parser("show-recipe", help="show one exact recipe without executing it")
    show.add_argument("recipe_id")
    show.add_argument("--require-ready", action="store_true")
    probe = sub.add_parser("probe-native", help="run only fixed version/help probes against a selected executable")
    probe.add_argument("--executable", default="gmx")
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
            result = show_recipe(args.recipe_id, args.require_ready)
        else:
            code, result = probe_native(args.executable)
    except ManualError as exc:
        code = 3 if exc.incomplete else 2
        result = {"status": "incomplete" if exc.incomplete else "blocked", "code": exc.code, "message": exc.message}
    except Exception:
        code = 4
        result = {"status": "internal-error", "code": "GROMACS.MANUAL.INTERNAL", "message": "Unexpected manual resolver failure."}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
