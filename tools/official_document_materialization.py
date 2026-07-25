#!/usr/bin/env python3
"""Fail-closed, read-only planning for exact official-document bytes."""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

from dataclasses import dataclass
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
from typing import Any, Mapping
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker


ADAPTER_ID = "explicit-user-materialization-v1"
ADAPTER_VERSION = "1.0"
MAX_SOURCE_BYTES = 268_435_456
READ_CHUNK_BYTES = 1024 * 1024
ERROR_SEVERITY = "error"


@dataclass(frozen=True, order=True)
class Finding:
    """One stable, location-bound validation failure."""

    code: str
    location: str
    message: str
    severity: str = ERROR_SEVERITY


@dataclass(frozen=True)
class ImportedSource:
    """One exact regular file read from a caller-supplied import root."""

    source_id: str
    import_path: str
    raw_sha256: str
    raw_bytes: int
    media_type: str
    content: bytes


@dataclass(frozen=True)
class ImportInspection:
    """Immutable result of inspecting an import root."""

    findings: tuple[Finding, ...]
    sources: tuple[ImportedSource, ...]


@dataclass(frozen=True)
class ArtifactPlan:
    """In-memory artifact manifest and proposed byte payloads."""

    findings: tuple[Finding, ...]
    manifest: dict[str, Any] | None
    proposed_bytes: Mapping[str, bytes]


@dataclass(frozen=True)
class EvaluationResult:
    """Complete evaluation result; no method in this module mutates files."""

    exit_code: int
    findings: tuple[Finding, ...]
    artifacts: tuple[dict[str, Any], ...]
    artifact_manifest: dict[str, Any] | None
    proposed_bytes: Mapping[str, bytes]
    mutation_performed: bool = False


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_schema(filename: str) -> dict[str, Any]:
    path = _repository_root() / "contracts" / filename
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{filename}: schema root must be an object")
    Draft202012Validator.check_schema(value)
    return value


_REQUEST_SCHEMA = _load_schema(
    "official-document-materialization-request.schema.json"
)
_MANIFEST_SCHEMA = _load_schema(
    "official-document-artifact-manifest.schema.json"
)
_REQUEST_VALIDATOR = Draft202012Validator(
    _REQUEST_SCHEMA,
    format_checker=FormatChecker(),
)
_MANIFEST_VALIDATOR = Draft202012Validator(
    _MANIFEST_SCHEMA,
    format_checker=FormatChecker(),
)


def _json_pointer(parts: object) -> str:
    encoded = [
        str(part).replace("~", "~0").replace("/", "~1")
        for part in parts  # type: ignore[union-attr]
    ]
    return "/" + "/".join(encoded) if encoded else "/"


def _ordered_findings(findings: list[Finding]) -> tuple[Finding, ...]:
    return tuple(
        sorted(
            set(findings),
            key=lambda item: (
                item.location,
                item.code,
                item.message,
                item.severity,
            ),
        )
    )


def _schema_findings(
    value: object,
    *,
    validator: Draft202012Validator,
    code: str,
) -> list[Finding]:
    findings: list[Finding] = []
    errors = sorted(
        validator.iter_errors(value),
        key=lambda error: (
            tuple(str(part) for part in error.absolute_path),
            error.message,
        ),
    )
    for error in errors:
        findings.append(
            Finding(
                code=code,
                location=_json_pointer(error.absolute_path),
                message=error.message,
            )
        )
    return findings


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _range_tuple(value: Mapping[str, Any]) -> tuple[int, int]:
    return int(value["start"]), int(value["end"])


def _range_value(interval: tuple[int, int]) -> dict[str, int]:
    return {"start": interval[0], "end": interval[1]}


def _duplicate_ids(
    values: list[Mapping[str, Any]],
    field: str,
) -> set[str]:
    seen: set[str] = set()
    duplicate: set[str] = set()
    for value in values:
        identifier = str(value[field])
        if identifier in seen:
            duplicate.add(identifier)
        seen.add(identifier)
    return duplicate


def _under_source_root(source_root: str, locator: str) -> bool:
    try:
        root = urlsplit(source_root)
        candidate = urlsplit(locator)
        root_port = root.port
        candidate_port = candidate.port
    except ValueError:
        return False
    if (
        root.scheme != "https"
        or candidate.scheme != "https"
        or root.username is not None
        or root.password is not None
        or candidate.username is not None
        or candidate.password is not None
        or root.fragment
        or root.query
        or candidate.fragment
        or root_port not in {None, 443}
        or candidate_port not in {None, 443}
        or root.hostname != candidate.hostname
        or root_port != candidate_port
    ):
        return False
    root_path = root.path.rstrip("/")
    candidate_path = candidate.path
    return candidate_path == root_path or candidate_path.startswith(
        f"{root_path}/"
    )


def _validate_interval_list(
    intervals: list[tuple[int, int]],
    *,
    total_bytes: int,
    location: str,
    prefix: str,
    findings: list[Finding],
) -> bool:
    valid = True
    previous_end: int | None = None
    for index, (start, end) in enumerate(intervals):
        item_location = f"{location}/{index}"
        if start >= end or end > total_bytes:
            findings.append(
                Finding(
                    code=f"{prefix}_RANGE_INVALID",
                    location=item_location,
                    message="byte range must be nonempty and confined to raw bytes",
                )
            )
            valid = False
        if previous_end is not None:
            if start < previous_end:
                findings.append(
                    Finding(
                        code=f"{prefix}_RANGE_OVERLAP",
                        location=item_location,
                        message="ordered byte ranges must not overlap",
                    )
                )
                valid = False
            elif start < intervals[index - 1][0]:
                findings.append(
                    Finding(
                        code=f"{prefix}_RANGE_ORDER_INVALID",
                        location=item_location,
                        message="byte ranges must be ordered by start offset",
                    )
                )
                valid = False
        previous_end = max(previous_end or 0, end)
    return valid


def _complement(
    intervals: list[tuple[int, int]],
    total_bytes: int,
) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    cursor = 0
    for start, end in intervals:
        if cursor < start:
            result.append((cursor, start))
        cursor = end
    if cursor < total_bytes:
        result.append((cursor, total_bytes))
    return result


def _segments_cover_preserved(
    segment_intervals: list[tuple[int, int]],
    preserved: list[tuple[int, int]],
    *,
    location: str,
    findings: list[Finding],
) -> None:
    target_index = 0
    cursor = preserved[0][0] if preserved else 0
    for index, interval in enumerate(segment_intervals):
        start, end = interval
        item_location = f"{location}/{index}/byte_range"
        if target_index >= len(preserved):
            findings.append(
                Finding(
                    code="SEGMENT_RANGE_OUTSIDE_PRESERVED",
                    location=item_location,
                    message="segment range is outside the preserved byte ranges",
                )
            )
            continue
        target_start, target_end = preserved[target_index]
        if start < cursor:
            findings.append(
                Finding(
                    code="SEGMENT_RANGE_OVERLAP",
                    location=item_location,
                    message="segment ranges overlap or move backwards",
                )
            )
            continue
        if start > cursor:
            if cursor == target_end and target_index + 1 < len(preserved):
                target_index += 1
                target_start, target_end = preserved[target_index]
                cursor = target_start
            if start > cursor:
                findings.append(
                    Finding(
                        code="SEGMENT_RANGE_GAP",
                        location=item_location,
                        message="segment ranges leave preserved bytes uncovered",
                    )
                )
        if start < target_start or end > target_end:
            findings.append(
                Finding(
                    code="SEGMENT_RANGE_OUTSIDE_PRESERVED",
                    location=item_location,
                    message="segment range crosses a preserved-range boundary",
                )
            )
            continue
        cursor = end
        if cursor == target_end and target_index + 1 < len(preserved):
            target_index += 1
            cursor = preserved[target_index][0]
    if preserved:
        final_end = preserved[-1][1]
        if target_index != len(preserved) - 1 or cursor != final_end:
            findings.append(
                Finding(
                    code="SEGMENT_RANGE_GAP",
                    location=location,
                    message="segment ranges do not exactly cover preserved bytes",
                )
            )


def validate_request(request: object) -> tuple[Finding, ...]:
    """Validate shape, provenance closure, and exact byte segmentation."""

    findings = _schema_findings(
        request,
        validator=_REQUEST_VALIDATOR,
        code="REQUEST_SCHEMA_INVALID",
    )
    if findings:
        return _ordered_findings(findings)

    assert isinstance(request, dict)
    included = request["included_sources"]
    exclusions = request["reviewed_exclusions"]
    subjects = request["subjects"]
    losses = request["losses"]

    included_ids = [source["source_id"] for source in included]
    excluded_ids = [source["source_id"] for source in exclusions]
    discovered_ids = request["discovered_sources"]
    overlap = set(included_ids).intersection(excluded_ids)
    if overlap:
        findings.append(
            Finding(
                code="CORPUS_PARTITION_OVERLAP",
                location="/discovered_sources",
                message="included and reviewed-exclusion source IDs must be disjoint",
            )
        )
    partition = set(included_ids).union(excluded_ids)
    if set(discovered_ids) != partition:
        findings.append(
            Finding(
                code="CORPUS_PARTITION_GAP",
                location="/discovered_sources",
                message="discovered sources must equal included union reviewed exclusions",
            )
        )
    for duplicate in sorted(_duplicate_ids(included, "source_id")):
        findings.append(
            Finding(
                code="SOURCE_ID_DUPLICATE",
                location="/included_sources",
                message=f"duplicate included source ID: {duplicate}",
            )
        )
    for duplicate in sorted(_duplicate_ids(exclusions, "source_id")):
        findings.append(
            Finding(
                code="EXCLUSION_ID_DUPLICATE",
                location="/reviewed_exclusions",
                message=f"duplicate reviewed-exclusion source ID: {duplicate}",
            )
        )

    subject_by_id: dict[str, Mapping[str, Any]] = {}
    for index, subject in enumerate(subjects):
        subject_id = subject["subject_id"]
        if subject_id in subject_by_id:
            findings.append(
                Finding(
                    code="SUBJECT_ID_DUPLICATE",
                    location=f"/subjects/{index}/subject_id",
                    message="subject ID must be globally unique",
                )
            )
        else:
            subject_by_id[subject_id] = subject

    loss_by_id: dict[str, Mapping[str, Any]] = {}
    for index, loss in enumerate(losses):
        loss_id = loss["loss_id"]
        if loss_id in loss_by_id:
            findings.append(
                Finding(
                    code="LOSS_ID_DUPLICATE",
                    location=f"/losses/{index}/loss_id",
                    message="loss ID must be globally unique",
                )
            )
        else:
            loss_by_id[loss_id] = loss

    global_segment_ids: dict[str, tuple[str, Mapping[str, Any]]] = {}
    import_paths: set[str] = set()
    output_paths: set[str] = set()
    for source_index, source in enumerate(included):
        source_id = source["source_id"]
        source_location = f"/included_sources/{source_index}"
        if not _under_source_root(request["source_root"], source["locator"]):
            findings.append(
                Finding(
                    code="SOURCE_LOCATOR_OUTSIDE_ROOT",
                    location=f"{source_location}/locator",
                    message="source locator must be confined to source_root",
                )
            )
        if source["import_path"] in import_paths:
            findings.append(
                Finding(
                    code="IMPORT_PATH_DUPLICATE",
                    location=f"{source_location}/import_path",
                    message="each included source requires a distinct import path",
                )
            )
        import_paths.add(source["import_path"])

        candidate_paths = [source["output_path"]] + [
            segment["output_path"] for segment in source["segments"]
        ]
        for path_index, output_path in enumerate(candidate_paths):
            if output_path in output_paths:
                path_location = (
                    f"{source_location}/output_path"
                    if path_index == 0
                    else f"{source_location}/segments/{path_index - 1}/output_path"
                )
                findings.append(
                    Finding(
                        code="OUTPUT_PATH_COLLISION",
                        location=path_location,
                        message="proposed artifact paths must be globally unique",
                    )
                )
            output_paths.add(output_path)

        raw_bytes = source["raw_bytes"]
        preservation = source["preservation"]
        if preservation["mode"] == "full-source":
            preserved = [(0, raw_bytes)]
        else:
            preserved = [
                _range_tuple(value)
                for value in preservation["preserved_ranges"]
            ]
            _validate_interval_list(
                preserved,
                total_bytes=raw_bytes,
                location=f"{source_location}/preservation/preserved_ranges",
                prefix="PRESERVED",
                findings=findings,
            )

        segment_intervals: list[tuple[int, int]] = []
        source_segment_ids: list[str] = []
        for segment_index, segment in enumerate(source["segments"]):
            segment_location = f"{source_location}/segments/{segment_index}"
            if segment["ordinal"] != segment_index:
                findings.append(
                    Finding(
                        code="SEGMENT_ORDINAL_INVALID",
                        location=f"{segment_location}/ordinal",
                        message="segment ordinals must be contiguous and match list order",
                    )
                )
            segment_id = segment["segment_id"]
            source_segment_ids.append(segment_id)
            if segment_id in global_segment_ids:
                findings.append(
                    Finding(
                        code="SEGMENT_ID_DUPLICATE",
                        location=f"{segment_location}/segment_id",
                        message="segment ID must be globally unique",
                    )
                )
            else:
                global_segment_ids[segment_id] = (source_id, segment)
            segment_intervals.append(_range_tuple(segment["byte_range"]))

        segments_valid = _validate_interval_list(
            segment_intervals,
            total_bytes=raw_bytes,
            location=f"{source_location}/segments",
            prefix="SEGMENT",
            findings=findings,
        )
        if segments_valid:
            _segments_cover_preserved(
                segment_intervals,
                preserved,
                location=f"{source_location}/segments",
                findings=findings,
            )

        declared_subject_ids = source["subject_ids"]
        expected_subject_ids = [
            subject["subject_id"]
            for subject in subjects
            if subject["source_id"] == source_id
        ]
        if set(declared_subject_ids) != set(expected_subject_ids):
            findings.append(
                Finding(
                    code="SOURCE_SUBJECT_CLOSURE_INVALID",
                    location=f"{source_location}/subject_ids",
                    message="source subject IDs must exactly match the subject ledger",
                )
            )
        for subject_id in declared_subject_ids:
            if subject_id not in subject_by_id:
                findings.append(
                    Finding(
                        code="SUBJECT_REFERENCE_UNKNOWN",
                        location=f"{source_location}/subject_ids",
                        message=f"unknown subject ID: {subject_id}",
                    )
                )

        declared_loss_ids = source["loss_ids"]
        expected_loss_ids = [
            loss["loss_id"]
            for loss in losses
            if loss["source_id"] == source_id
        ]
        if set(declared_loss_ids) != set(expected_loss_ids):
            findings.append(
                Finding(
                    code="SOURCE_LOSS_CLOSURE_INVALID",
                    location=f"{source_location}/loss_ids",
                    message="source loss IDs must exactly match the loss ledger",
                )
            )
        ordered_loss_ranges: list[tuple[int, int]] = []
        for loss_id in declared_loss_ids:
            loss = loss_by_id.get(loss_id)
            if loss is None:
                findings.append(
                    Finding(
                        code="LOSS_REFERENCE_UNKNOWN",
                        location=f"{source_location}/loss_ids",
                        message=f"unknown loss ID: {loss_id}",
                    )
                )
                continue
            if loss["source_id"] != source_id:
                findings.append(
                    Finding(
                        code="LOSS_SOURCE_MISMATCH",
                        location=f"{source_location}/loss_ids",
                        message="loss ledger source does not match the source reference",
                    )
                )
                continue
            ordered_loss_ranges.append(_range_tuple(loss["byte_range"]))
        if ordered_loss_ranges != _complement(preserved, raw_bytes):
            findings.append(
                Finding(
                    code="LOSS_RANGE_CLOSURE_INVALID",
                    location=f"{source_location}/loss_ids",
                    message="loss ranges must exactly cover bytes outside preserved ranges",
                )
            )

        source_segment_set = set(source_segment_ids)
        for subject_id in declared_subject_ids:
            subject = subject_by_id.get(subject_id)
            if subject is None or subject["source_id"] != source_id:
                continue
            if not set(subject["segment_ids"]).issubset(source_segment_set):
                findings.append(
                    Finding(
                        code="SUBJECT_SEGMENT_SOURCE_MISMATCH",
                        location=f"/subjects/{subjects.index(subject)}/segment_ids",
                        message="subject segments must belong to the same source",
                    )
                )
        for segment_index, segment in enumerate(source["segments"]):
            reverse_subject_ids = {
                subject["subject_id"]
                for subject in subjects
                if segment["segment_id"] in subject["segment_ids"]
            }
            if set(segment["subject_ids"]) != reverse_subject_ids:
                findings.append(
                    Finding(
                        code="SEGMENT_SUBJECT_CLOSURE_INVALID",
                        location=(
                            f"{source_location}/segments/{segment_index}/subject_ids"
                        ),
                        message="segment subject IDs must exactly match reverse ledger references",
                    )
                )

    included_id_set = set(included_ids)
    for subject_index, subject in enumerate(subjects):
        if subject["source_id"] not in included_id_set:
            findings.append(
                Finding(
                    code="SUBJECT_SOURCE_UNKNOWN",
                    location=f"/subjects/{subject_index}/source_id",
                    message="subject source must be included",
                )
            )
        for segment_id in subject["segment_ids"]:
            segment = global_segment_ids.get(segment_id)
            if segment is None:
                findings.append(
                    Finding(
                        code="SUBJECT_SEGMENT_UNKNOWN",
                        location=f"/subjects/{subject_index}/segment_ids",
                        message=f"unknown segment ID: {segment_id}",
                    )
                )
            elif segment[0] != subject["source_id"]:
                findings.append(
                    Finding(
                        code="SUBJECT_SEGMENT_SOURCE_MISMATCH",
                        location=f"/subjects/{subject_index}/segment_ids",
                        message="subject and segment must reference the same source",
                    )
                )
    for loss_index, loss in enumerate(losses):
        if loss["source_id"] not in included_id_set:
            findings.append(
                Finding(
                    code="LOSS_SOURCE_UNKNOWN",
                    location=f"/losses/{loss_index}/source_id",
                    message="loss source must be included",
                )
            )

    if (
        request["content_mode"] == "materialize"
        and not included
    ):
        findings.append(
            Finding(
                code="MATERIALIZE_SOURCE_MISSING",
                location="/included_sources",
                message="materialize mode requires at least one included source",
            )
        )

    return _ordered_findings(findings)


def _stat_identity(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _path_error_code(exc: OSError) -> str:
    if exc.errno == errno.ENOENT:
        return "IMPORT_PATH_MISSING"
    if exc.errno in {errno.ELOOP, errno.EMLINK}:
        return "IMPORT_PATH_SYMLINK"
    if exc.errno in {errno.ENOTDIR, errno.EISDIR}:
        return "IMPORT_PATH_NOT_REGULAR"
    return "IMPORT_PATH_IO_ERROR"


def _open_confined_regular(
    root_fd: int,
    import_path: str,
) -> tuple[int | None, os.stat_result | None, Finding | None]:
    location = f"/included_sources/{import_path}"
    parts = PurePosixPath(import_path).parts
    current_fd = os.dup(root_fd)
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directory_flags |= getattr(os, "O_CLOEXEC", 0)
    try:
        for component in parts[:-1]:
            try:
                before = os.stat(
                    component,
                    dir_fd=current_fd,
                    follow_symlinks=False,
                )
                if stat.S_ISLNK(before.st_mode):
                    return (
                        None,
                        None,
                        Finding(
                            "IMPORT_PATH_SYMLINK",
                            location,
                            "import path contains a symbolic link",
                        ),
                    )
                if not stat.S_ISDIR(before.st_mode):
                    return (
                        None,
                        None,
                        Finding(
                            "IMPORT_PATH_NOT_REGULAR",
                            location,
                            "import path parent is not a directory",
                        ),
                    )
                next_fd = os.open(
                    component,
                    directory_flags,
                    dir_fd=current_fd,
                )
            except OSError as exc:
                return (
                    None,
                    None,
                    Finding(
                        _path_error_code(exc),
                        location,
                        "cannot safely open import path parent",
                    ),
                )
            after = os.fstat(next_fd)
            if before.st_dev != after.st_dev or before.st_ino != after.st_ino:
                os.close(next_fd)
                return (
                    None,
                    None,
                    Finding(
                        "IMPORT_PATH_MUTATED",
                        location,
                        "import path parent changed while being opened",
                    ),
                )
            os.close(current_fd)
            current_fd = next_fd

        leaf = parts[-1]
        try:
            path_before = os.stat(
                leaf,
                dir_fd=current_fd,
                follow_symlinks=False,
            )
            if stat.S_ISLNK(path_before.st_mode):
                return (
                    None,
                    None,
                    Finding(
                        "IMPORT_PATH_SYMLINK",
                        location,
                        "import path is a symbolic link",
                    ),
                )
            file_flags = os.O_RDONLY | os.O_NOFOLLOW
            file_flags |= getattr(os, "O_CLOEXEC", 0)
            file_flags |= getattr(os, "O_NONBLOCK", 0)
            file_fd = os.open(leaf, file_flags, dir_fd=current_fd)
        except OSError as exc:
            return (
                None,
                None,
                Finding(
                    _path_error_code(exc),
                    location,
                    "cannot safely open import file",
                ),
            )
        opened = os.fstat(file_fd)
        if (
            path_before.st_dev != opened.st_dev
            or path_before.st_ino != opened.st_ino
        ):
            os.close(file_fd)
            return (
                None,
                None,
                Finding(
                    "IMPORT_PATH_MUTATED",
                    location,
                    "import file changed while being opened",
                ),
            )
        if not stat.S_ISREG(opened.st_mode):
            os.close(file_fd)
            return (
                None,
                None,
                Finding(
                    "IMPORT_PATH_NOT_REGULAR",
                    location,
                    "import path must identify a regular file",
                ),
            )
        if opened.st_nlink != 1:
            os.close(file_fd)
            return (
                None,
                None,
                Finding(
                    "IMPORT_PATH_HARDLINK",
                    location,
                    "import file must have exactly one hard link",
                ),
            )
        return file_fd, opened, None
    finally:
        os.close(current_fd)


def _inspect_source(
    root_fd: int,
    source: Mapping[str, Any],
) -> tuple[ImportedSource | None, Finding | None]:
    source_id = source["source_id"]
    location = f"/included_sources/{source_id}/import_path"
    file_fd, before, opening_error = _open_confined_regular(
        root_fd,
        source["import_path"],
    )
    if opening_error is not None:
        return (
            None,
            Finding(
                opening_error.code,
                location,
                opening_error.message,
            ),
        )
    assert file_fd is not None and before is not None
    try:
        if before.st_size != source["raw_bytes"]:
            return (
                None,
                Finding(
                    "IMPORT_PATH_SIZE_MISMATCH",
                    location,
                    "regular-file size does not match declared raw_bytes",
                ),
            )
        if before.st_size > MAX_SOURCE_BYTES:
            return (
                None,
                Finding(
                    "IMPORT_PATH_SIZE_LIMIT",
                    location,
                    "import file exceeds the adapter byte limit",
                ),
            )

        chunks: list[bytes] = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(file_fd, min(READ_CHUNK_BYTES, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        trailing = os.read(file_fd, 1)
        content = b"".join(chunks)
        after = os.fstat(file_fd)
        if (
            remaining != 0
            or trailing
            or _stat_identity(before) != _stat_identity(after)
        ):
            return (
                None,
                Finding(
                    "IMPORT_PATH_MUTATED",
                    location,
                    "import file identity changed during the exact-byte read",
                ),
            )
        verify_fd, verify_status, verify_error = _open_confined_regular(
            root_fd,
            source["import_path"],
        )
        if verify_error is not None or verify_fd is None or verify_status is None:
            if verify_fd is not None:
                os.close(verify_fd)
            return (
                None,
                Finding(
                    "IMPORT_PATH_MUTATED",
                    location,
                    "import path changed after the exact-byte read",
                ),
            )
        try:
            if _stat_identity(after) != _stat_identity(verify_status):
                return (
                    None,
                    Finding(
                        "IMPORT_PATH_MUTATED",
                        location,
                        "import path identity changed after the exact-byte read",
                    ),
                )
        finally:
            os.close(verify_fd)
        digest = hashlib.sha256(content).hexdigest()
        if digest != source["raw_sha256"]:
            return (
                None,
                Finding(
                    "IMPORT_PATH_HASH_MISMATCH",
                    location,
                    "exact import bytes do not match declared raw_sha256",
                ),
            )
        return (
            ImportedSource(
                source_id=source_id,
                import_path=source["import_path"],
                raw_sha256=digest,
                raw_bytes=len(content),
                media_type=source["media_type"],
                content=content,
            ),
            None,
        )
    except OSError:
        return (
            None,
            Finding(
                "IMPORT_PATH_IO_ERROR",
                location,
                "exact-byte read failed",
            ),
        )
    finally:
        os.close(file_fd)


def inspect_import_root(
    request: object,
    import_root: Path,
) -> ImportInspection:
    """Read exact source bytes without following links or mutating the root."""

    request_findings = validate_request(request)
    if request_findings:
        return ImportInspection(request_findings, ())
    assert isinstance(request, dict)
    if request["content_mode"] == "external-only":
        return ImportInspection((), ())
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        return ImportInspection(
            (
                Finding(
                    "IMPORT_NOFOLLOW_UNAVAILABLE",
                    "/import_root",
                    "platform cannot provide the required no-follow file opens",
                ),
            ),
            (),
        )

    root_location = "/import_root"
    try:
        root_lstat = os.lstat(import_root)
        if stat.S_ISLNK(root_lstat.st_mode):
            return ImportInspection(
                (
                    Finding(
                        "IMPORT_ROOT_SYMLINK",
                        root_location,
                        "import root must not be a symbolic link",
                    ),
                ),
                (),
            )
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        flags |= getattr(os, "O_CLOEXEC", 0)
        root_fd = os.open(os.fspath(import_root), flags)
    except OSError:
        return ImportInspection(
            (
                Finding(
                    "IMPORT_ROOT_UNAVAILABLE",
                    root_location,
                    "cannot safely open import root",
                ),
            ),
            (),
        )

    findings: list[Finding] = []
    imported: list[ImportedSource] = []
    try:
        root_before = os.fstat(root_fd)
        if (
            root_lstat.st_dev != root_before.st_dev
            or root_lstat.st_ino != root_before.st_ino
        ):
            findings.append(
                Finding(
                    "IMPORT_ROOT_MUTATED",
                    root_location,
                    "import root changed while being opened",
                )
            )
        elif not stat.S_ISDIR(root_before.st_mode):
            findings.append(
                Finding(
                    "IMPORT_ROOT_NOT_DIRECTORY",
                    root_location,
                    "import root must be a directory",
                )
            )
        else:
            for source in sorted(
                request["included_sources"],
                key=lambda value: value["source_id"],
            ):
                record, finding = _inspect_source(root_fd, source)
                if finding is not None:
                    findings.append(finding)
                elif record is not None:
                    imported.append(record)
        root_after = os.fstat(root_fd)
        if (
            root_before.st_dev != root_after.st_dev
            or root_before.st_ino != root_after.st_ino
            or root_before.st_mode != root_after.st_mode
        ):
            findings.append(
                Finding(
                    "IMPORT_ROOT_MUTATED",
                    root_location,
                    "import root identity changed during inspection",
                )
            )
    finally:
        os.close(root_fd)
    return ImportInspection(
        _ordered_findings(findings),
        tuple(sorted(imported, key=lambda value: value.source_id)),
    )


def _artifact_id(value: Mapping[str, Any]) -> str:
    return "artifact-" + hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _lineage(
    request: Mapping[str, Any],
    source: Mapping[str, Any],
    byte_range: dict[str, int] | None,
) -> dict[str, Any]:
    return {
        "request_id": request["request_id"],
        "authority_id": request["authority_id"],
        "provider_id": request["provider_id"],
        "version": request["version"],
        "revision": request["revision"],
        "source_id": source["source_id"],
        "source_locator": source["locator"],
        "source_raw_sha256": source["raw_sha256"],
        "source_raw_bytes": source["raw_bytes"],
        "byte_range": byte_range,
    }


def _artifact(
    *,
    request: Mapping[str, Any],
    source: Mapping[str, Any],
    role: str,
    path: str,
    content: bytes,
    mode: str,
    segment_id: str | None,
    byte_range: dict[str, int] | None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "role": role,
        "path": path,
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "media_type": source["media_type"],
        "mode": mode,
        "source_id": source["source_id"],
        "segment_id": segment_id,
        "lineage": _lineage(request, source, byte_range),
    }
    return {"artifact_id": _artifact_id(value), **value}


def plan_artifacts(
    request: object,
    imported: ImportInspection,
) -> ArtifactPlan:
    """Create a deterministic manifest and byte map entirely in memory."""

    findings = list(validate_request(request))
    findings.extend(imported.findings)
    if findings:
        return ArtifactPlan(_ordered_findings(findings), None, {})
    assert isinstance(request, dict)
    if request["content_mode"] == "external-only":
        return ArtifactPlan((), None, {})

    imported_by_id = {record.source_id: record for record in imported.sources}
    expected_ids = {
        source["source_id"] for source in request["included_sources"]
    }
    if set(imported_by_id) != expected_ids:
        return ArtifactPlan(
            (
                Finding(
                    "IMPORTED_SOURCE_SET_MISMATCH",
                    "/included_sources",
                    "inspected source IDs must exactly match included sources",
                ),
            ),
            None,
            {},
        )

    artifacts: list[dict[str, Any]] = []
    proposed: dict[str, bytes] = {}
    for source in sorted(
        request["included_sources"],
        key=lambda value: value["source_id"],
    ):
        imported_source = imported_by_id[source["source_id"]]
        if (
            imported_source.import_path != source["import_path"]
            or imported_source.raw_sha256 != source["raw_sha256"]
            or imported_source.raw_bytes != source["raw_bytes"]
            or imported_source.media_type != source["media_type"]
            or hashlib.sha256(imported_source.content).hexdigest()
            != source["raw_sha256"]
        ):
            findings.append(
                Finding(
                    "IMPORTED_SOURCE_IDENTITY_MISMATCH",
                    f"/included_sources/{source['source_id']}",
                    "inspected source metadata or bytes changed before planning",
                )
            )
            continue

        proposed[source["output_path"]] = imported_source.content
        artifacts.append(
            _artifact(
                request=request,
                source=source,
                role="raw-source",
                path=source["output_path"],
                content=imported_source.content,
                mode="exact-source-copy",
                segment_id=None,
                byte_range=None,
            )
        )
        for segment in sorted(
            source["segments"],
            key=lambda value: value["ordinal"],
        ):
            start, end = _range_tuple(segment["byte_range"])
            content = imported_source.content[start:end]
            proposed[segment["output_path"]] = content
            artifacts.append(
                _artifact(
                    request=request,
                    source=source,
                    role="document-segment",
                    path=segment["output_path"],
                    content=content,
                    mode="exact-byte-range",
                    segment_id=segment["segment_id"],
                    byte_range=_range_value((start, end)),
                )
            )

    if findings:
        return ArtifactPlan(_ordered_findings(findings), None, {})
    artifacts.sort(
        key=lambda value: (
            value["path"],
            value["role"],
            value["artifact_id"],
        )
    )
    request_sha256 = hashlib.sha256(_canonical_json_bytes(request)).hexdigest()
    manifest_without_id: dict[str, Any] = {
        "schema_version": "1.0",
        "contract_name": "official-document-artifact-manifest",
        "adapter_id": ADAPTER_ID,
        "request_id": request["request_id"],
        "request_sha256": request_sha256,
        "request_hash_basis": "canonical-json-sort-keys-utf8-v1",
        "authority_id": request["authority_id"],
        "provider_id": request["provider_id"],
        "version": request["version"],
        "revision": request["revision"],
        "artifacts": artifacts,
    }
    manifest_id = "manifest-" + hashlib.sha256(
        _canonical_json_bytes(manifest_without_id)
    ).hexdigest()
    manifest = {"manifest_id": manifest_id, **manifest_without_id}
    manifest_findings = _schema_findings(
        manifest,
        validator=_MANIFEST_VALIDATOR,
        code="ARTIFACT_MANIFEST_SCHEMA_INVALID",
    )
    if manifest_findings:
        return ArtifactPlan(
            _ordered_findings(manifest_findings),
            None,
            {},
        )
    return ArtifactPlan(
        (),
        manifest,
        dict(sorted(proposed.items())),
    )


def evaluate_request(
    request: object,
    import_root: Path | None = None,
) -> EvaluationResult:
    """Evaluate one request without network access or filesystem mutation."""

    findings = validate_request(request)
    if findings:
        return EvaluationResult(2, findings, (), None, {})
    assert isinstance(request, dict)
    if request["content_mode"] == "external-only":
        return EvaluationResult(0, (), (), None, {})
    if import_root is None:
        missing = (
            Finding(
                "IMPORT_ROOT_REQUIRED",
                "/import_root",
                "materialize mode requires a caller-supplied import root",
            ),
        )
        return EvaluationResult(2, missing, (), None, {})

    inspection = inspect_import_root(request, Path(import_root))
    if inspection.findings:
        return EvaluationResult(2, inspection.findings, (), None, {})
    planned = plan_artifacts(request, inspection)
    if planned.findings or planned.manifest is None:
        effective = planned.findings or (
            Finding(
                "ARTIFACT_PLAN_EMPTY",
                "/included_sources",
                "materialize mode did not produce an artifact plan",
            ),
        )
        return EvaluationResult(2, effective, (), None, {})
    return EvaluationResult(
        exit_code=0,
        findings=(),
        artifacts=tuple(planned.manifest["artifacts"]),
        artifact_manifest=planned.manifest,
        proposed_bytes=planned.proposed_bytes,
    )
