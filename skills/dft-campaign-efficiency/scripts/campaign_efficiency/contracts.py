from __future__ import annotations

from pathlib import Path
import sys


for _parent in Path(__file__).resolve().parents:
    if _parent.joinpath("tools", "registry_snapshot.py").is_file():
        _tools = str(_parent / "tools")
        if _tools not in sys.path:
            sys.path.insert(0, _tools)
        break
else:  # pragma: no cover - installation layout is checked by the caller
    raise RuntimeError("cannot locate shared registry snapshot loader")

from registry_snapshot import RegistrySnapshot, load_registry_snapshot  # noqa: E402
from validate_contract import validation_errors as catalog_validation_errors  # noqa: E402


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
    raise RuntimeError("cannot locate Vibe-DFT-Skills repository root")


def calculation_codes(snapshot: RegistrySnapshot | None = None) -> tuple[str, ...]:
    selected = snapshot or load_registry_snapshot(repo_root())
    return selected.calculation_codes()


def errors(kind: str, value: object) -> list[str]:
    if kind not in SCHEMAS:
        return [f"<selector>: unknown campaign contract kind {kind!r}"]
    return catalog_validation_errors(
        kind,
        value,
        repo_root() / "contracts",
    )
