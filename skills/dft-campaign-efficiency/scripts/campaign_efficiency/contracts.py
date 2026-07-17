from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


SCHEMAS = {
    "run": "run-manifest.schema.json",
    "campaign": "campaign-record.schema.json",
    "recommendation": "recommendation-record.schema.json",
}


def repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if parent.joinpath("contracts").is_dir() and parent.joinpath("skills").is_dir():
            return parent
    raise RuntimeError("cannot locate DFT-Codex-Skills repository root")


def errors(kind: str, value: object) -> list[str]:
    schema = json.loads((repo_root() / "contracts" / SCHEMAS[kind]).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    failures = []
    for error in sorted(validator.iter_errors(value), key=lambda item: list(item.absolute_path)):
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        failures.append(f"{location}: {error.message}")
    return failures
