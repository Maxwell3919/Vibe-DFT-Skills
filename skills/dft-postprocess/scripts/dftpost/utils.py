from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
    temporary.replace(path)


def relative_file(root: Path, value: Path) -> tuple[Path, str]:
    root = root.resolve()
    path = value if value.is_absolute() else root / value
    path = path.resolve()
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"artifact path is outside root: {value}") from exc
    if not path.is_file():
        raise ValueError(f"artifact file is missing: {value}")
    return path, relative.as_posix()


def find_repo_root(start: Path) -> Path:
    for parent in (start.resolve(), *start.resolve().parents):
        if parent.joinpath("contracts").is_dir() and parent.joinpath("skills").is_dir():
            return parent
    raise RuntimeError("cannot locate Vibe-DFT-Skills repository root")
