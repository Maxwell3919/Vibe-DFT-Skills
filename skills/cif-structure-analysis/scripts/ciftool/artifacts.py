from __future__ import annotations

import ctypes
import errno
import os
from pathlib import Path
import secrets
import stat
from typing import Iterable


class ArtifactPublishError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


def _absolute_key(path: Path) -> str:
    return os.path.normcase(os.path.abspath(os.fspath(path)))


def _inspect_real_directory_chain(
    directory: Path,
    *,
    allow_missing: bool,
) -> None:
    absolute = Path(os.path.abspath(os.fspath(directory)))
    current = Path(absolute.anchor)
    components = absolute.parts[1:]
    for component in components:
        current = current / component
        try:
            info = current.lstat()
        except FileNotFoundError:
            if allow_missing:
                return
            raise ArtifactPublishError(
                "OUTPUT_PARENT_INVALID",
                "output parent or one of its ancestors does not exist",
            )
        except OSError as exc:
            raise ArtifactPublishError(
                "OUTPUT_PARENT_INVALID",
                "output parent ancestry could not be inspected",
            ) from exc
        if stat.S_ISLNK(info.st_mode):
            raise ArtifactPublishError(
                "OUTPUT_PARENT_INVALID",
                "symlinks are refused in the complete output parent ancestry",
            )
        if not stat.S_ISDIR(info.st_mode):
            raise ArtifactPublishError(
                "OUTPUT_PARENT_INVALID",
                "every existing output ancestor must be a directory",
            )


def validate_output_parent(parent: Path, *, create: bool) -> None:
    """Reject symlinks in every existing ancestor and validate the leaf parent."""

    _inspect_real_directory_chain(parent, allow_missing=create)
    try:
        if create:
            parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ArtifactPublishError(
            "OUTPUT_PARENT_INVALID",
            "output parent could not be prepared",
        ) from exc
    _inspect_real_directory_chain(parent, allow_missing=False)


def _ensure_real_parent(parent: Path) -> None:
    validate_output_parent(parent, create=True)


def validate_target_graph(targets: Iterable[Path]) -> tuple[Path, ...]:
    selected = tuple(targets)
    keys = [_absolute_key(path) for path in selected]
    if len(keys) != len(set(keys)):
        raise ArtifactPublishError(
            "OUTPUT_COLLISION",
            "artifact target paths must be distinct",
        )
    for target in selected:
        if not target.name or target.name in {".", ".."}:
            raise ArtifactPublishError(
                "OUTPUT_PATH_INVALID",
                "each artifact must name a new regular file",
            )
        _ensure_real_parent(target.parent)
        try:
            target.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise ArtifactPublishError(
                "OUTPUT_PREFLIGHT_FAILED",
                "artifact target could not be inspected",
            ) from exc
        raise ArtifactPublishError(
            "OUTPUT_EXISTS",
            "an artifact target already exists; overwrite is refused",
        )
    return selected


def _same_inode(left: os.stat_result, right: os.stat_result) -> bool:
    return left.st_dev == right.st_dev and left.st_ino == right.st_ino


def publish_files_no_clobber(payloads: Iterable[tuple[Path, bytes]]) -> None:
    """Publish a new loose artifact set and roll back this set on any failure."""

    entries = tuple(payloads)
    targets = validate_target_graph(target for target, _ in entries)
    staged: list[tuple[Path, Path, os.stat_result]] = []
    published: list[tuple[Path, os.stat_result]] = []
    completed = False
    try:
        for target, payload in entries:
            temporary = target.parent / (
                f".{target.name}.candidate-{secrets.token_hex(8)}.tmp"
            )
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(temporary, flags, 0o600)
            try:
                with os.fdopen(descriptor, "wb", closefd=True) as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
            except Exception:
                temporary.unlink(missing_ok=True)
                raise
            staged.append((temporary, target, temporary.lstat()))

        validate_target_graph(targets)
        for temporary, target, temporary_info in staged:
            try:
                os.link(temporary, target, follow_symlinks=False)
            except FileExistsError as exc:
                raise ArtifactPublishError(
                    "OUTPUT_EXISTS",
                    "an artifact target appeared concurrently; overwrite is refused",
                ) from exc
            final_info = target.lstat()
            if not _same_inode(temporary_info, final_info):
                raise ArtifactPublishError(
                    "OUTPUT_IDENTITY_MISMATCH",
                    "published artifact identity does not match its staged bytes",
                )
            published.append((target, temporary_info))
        for parent in {target.parent for target in targets}:
            flags = os.O_RDONLY
            if hasattr(os, "O_DIRECTORY"):
                flags |= os.O_DIRECTORY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(parent, flags)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        completed = True
    except ArtifactPublishError:
        raise
    except OSError as exc:
        raise ArtifactPublishError(
            "OUTPUT_WRITE_FAILED",
            "artifact set could not be published safely",
        ) from exc
    finally:
        if not completed:
            for target, expected in reversed(published):
                try:
                    current = target.lstat()
                    if _same_inode(current, expected):
                        target.unlink()
                except OSError:
                    pass
        for temporary, _, _ in staged:
            temporary.unlink(missing_ok=True)


def write_private_file(path: Path, payload: bytes) -> None:
    _ensure_real_parent(path.parent)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise ArtifactPublishError(
            "STAGING_WRITE_FAILED",
            "private staged artifact could not be written",
        ) from exc


def publish_bundle_no_clobber(staged_directory: Path, target_directory: Path) -> None:
    """Atomically publish one complete directory with Linux renameat2 no-replace."""

    try:
        staged_info = staged_directory.lstat()
    except OSError as exc:
        raise ArtifactPublishError(
            "BUNDLE_STAGE_INVALID",
            "staged bundle directory is unavailable",
        ) from exc
    if stat.S_ISLNK(staged_info.st_mode) or not stat.S_ISDIR(staged_info.st_mode):
        raise ArtifactPublishError(
            "BUNDLE_STAGE_INVALID",
            "staged bundle must be a real directory",
        )
    if not target_directory.name or target_directory.name in {".", ".."}:
        raise ArtifactPublishError(
            "OUTPUT_PATH_INVALID",
            "bundle target must name a new directory",
        )
    _ensure_real_parent(target_directory.parent)
    try:
        target_directory.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise ArtifactPublishError(
            "OUTPUT_PREFLIGHT_FAILED",
            "bundle target could not be inspected",
        ) from exc
    else:
        raise ArtifactPublishError(
            "OUTPUT_EXISTS",
            "bundle target already exists; overwrite is refused",
        )

    directories: list[Path] = []
    for root, names, filenames in os.walk(staged_directory):
        root_path = Path(root)
        directories.append(root_path)
        for name in names:
            child = root_path / name
            child_info = child.lstat()
            if stat.S_ISLNK(child_info.st_mode) or not stat.S_ISDIR(
                child_info.st_mode
            ):
                raise ArtifactPublishError(
                    "BUNDLE_STAGE_INVALID",
                    "staged bundle contains a non-directory child",
                )
        for name in filenames:
            child = root_path / name
            child_info = child.lstat()
            if stat.S_ISLNK(child_info.st_mode) or not stat.S_ISREG(
                child_info.st_mode
            ):
                raise ArtifactPublishError(
                    "BUNDLE_STAGE_INVALID",
                    "staged bundle contains a non-regular artifact",
                )
            descriptor = os.open(child, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    for directory in reversed(directories):
        flags = os.O_RDONLY
        if hasattr(os, "O_DIRECTORY"):
            flags |= os.O_DIRECTORY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(directory, flags)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    library = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(library, "renameat2", None)
    if renameat2 is None:
        raise ArtifactPublishError(
            "ATOMIC_BUNDLE_UNAVAILABLE",
            "renameat2 no-replace support is required for atomic bundle publication",
        )
    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    result = renameat2(
        -100,
        os.fsencode(staged_directory),
        -100,
        os.fsencode(target_directory),
        1,
    )
    if result != 0:
        error_number = ctypes.get_errno()
        if error_number in {errno.EEXIST, errno.ENOTEMPTY}:
            raise ArtifactPublishError(
                "OUTPUT_EXISTS",
                "bundle target appeared concurrently; overwrite is refused",
            )
        raise ArtifactPublishError(
            "ATOMIC_BUNDLE_FAILED",
            f"atomic bundle publication failed with errno {error_number}",
        )

    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(target_directory.parent, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
