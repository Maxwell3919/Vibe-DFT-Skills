from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping


def external_fixture_root(
    environment: Mapping[str, str] | None = None,
    repository_root: Path | None = None,
) -> Path | None:
    selected_environment = os.environ if environment is None else environment
    value = selected_environment.get("DFTPOST_FIXTURE_ROOT")
    if not value:
        return None
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"DFTPOST_FIXTURE_ROOT is not a directory: {root}")
    if repository_root is not None:
        repository = repository_root.resolve()
        try:
            root.relative_to(repository)
        except ValueError:
            pass
        else:
            raise ValueError("DFTPOST_FIXTURE_ROOT must stay outside the source repository")
    return root


def fixture_case(relative_path: str, root: Path) -> Path:
    if not relative_path:
        raise ValueError("fixture case path must not be empty")
    selected = (root.resolve() / relative_path).resolve()
    try:
        selected.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"fixture case escapes root: {relative_path}") from exc
    if not selected.is_dir():
        raise ValueError(f"fixture case is not a directory: {relative_path}")
    return selected
