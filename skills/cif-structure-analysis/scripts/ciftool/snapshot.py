from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import stat


MAX_CIF_BYTES = 64 * 1024 * 1024


class SnapshotError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True)
class InputSnapshot:
    path: Path
    source_name: str
    size_bytes: int
    mtime: float
    sha256: str


def _stat_identity(info: os.stat_result) -> tuple[int, int, int, int, int, int, int]:
    return (
        info.st_dev,
        info.st_ino,
        stat.S_IFMT(info.st_mode),
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
        info.st_nlink,
    )


def _safe_suffix(path: Path) -> str:
    suffix = path.suffix.lower()
    return suffix if re.fullmatch(r"\.[a-z0-9]{1,10}", suffix) else ".cif"


def capture_input_snapshot(
    source_path: Path,
    snapshot_directory: Path,
    *,
    max_bytes: int = MAX_CIF_BYTES,
) -> InputSnapshot:
    """Bind one regular-file read to a task-private immutable parser snapshot."""

    if max_bytes <= 0:
        raise ValueError("max_bytes must be greater than zero")
    try:
        initial = source_path.lstat()
    except OSError as exc:
        raise SnapshotError("INPUT_UNREADABLE", "input CIF is unavailable") from exc
    if stat.S_ISLNK(initial.st_mode) or not stat.S_ISREG(initial.st_mode):
        raise SnapshotError(
            "INPUT_NOT_REGULAR",
            "symlinks and non-regular CIF inputs are refused",
        )
    if initial.st_size > max_bytes:
        raise SnapshotError(
            "INPUT_TOO_LARGE",
            f"input CIF exceeds the {max_bytes}-byte safety limit",
        )

    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(source_path, flags)
    except OSError as exc:
        raise SnapshotError(
            "INPUT_UNREADABLE",
            "input CIF could not be opened safely",
        ) from exc

    try:
        with os.fdopen(descriptor, "rb", closefd=True) as handle:
            opened = os.fstat(handle.fileno())
            if (
                not stat.S_ISREG(opened.st_mode)
                or _stat_identity(opened) != _stat_identity(initial)
            ):
                raise SnapshotError(
                    "INPUT_CHANGED_DURING_CAPTURE",
                    "input CIF identity changed before capture",
                )
            chunks: list[bytes] = []
            captured = 0
            while True:
                chunk = handle.read(min(1024 * 1024, max_bytes + 1 - captured))
                if not chunk:
                    break
                chunks.append(chunk)
                captured += len(chunk)
                if captured > max_bytes:
                    raise SnapshotError(
                        "INPUT_TOO_LARGE",
                        f"input CIF exceeds the {max_bytes}-byte safety limit",
                    )
            finished = os.fstat(handle.fileno())
    except SnapshotError:
        raise
    except OSError as exc:
        raise SnapshotError(
            "INPUT_UNREADABLE",
            "input CIF could not be read safely",
        ) from exc

    try:
        final_path = source_path.lstat()
    except OSError as exc:
        raise SnapshotError(
            "INPUT_CHANGED_DURING_CAPTURE",
            "input CIF disappeared during capture",
        ) from exc
    raw = b"".join(chunks)
    if (
        _stat_identity(finished) != _stat_identity(opened)
        or _stat_identity(final_path) != _stat_identity(opened)
        or len(raw) != finished.st_size
        or stat.S_ISLNK(final_path.st_mode)
    ):
        raise SnapshotError(
            "INPUT_CHANGED_DURING_CAPTURE",
            "input CIF path or bytes changed during capture",
        )

    digest = hashlib.sha256(raw).hexdigest()
    try:
        directory_info = snapshot_directory.lstat()
    except OSError as exc:
        raise SnapshotError(
            "SNAPSHOT_DIRECTORY_INVALID",
            "snapshot directory is unavailable",
        ) from exc
    if stat.S_ISLNK(directory_info.st_mode) or not stat.S_ISDIR(directory_info.st_mode):
        raise SnapshotError(
            "SNAPSHOT_DIRECTORY_INVALID",
            "snapshot directory must be a real directory",
        )
    snapshot_path = (
        snapshot_directory / f"source-{digest[:16]}{_safe_suffix(source_path)}"
    )
    create_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        create_flags |= os.O_NOFOLLOW
    try:
        snapshot_descriptor = os.open(snapshot_path, create_flags, 0o600)
        with os.fdopen(snapshot_descriptor, "wb", closefd=True) as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise SnapshotError(
            "SNAPSHOT_WRITE_FAILED",
            "task-private CIF snapshot could not be created",
        ) from exc

    return InputSnapshot(
        path=snapshot_path,
        source_name=source_path.name,
        size_bytes=len(raw),
        mtime=float(opened.st_mtime),
        sha256=digest,
    )
