#!/usr/bin/env python3
"""Shared strict UTF-8 JSON parser for trust-boundary validators."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import stat
from typing import Any


DEFAULT_MAX_BYTES = 64 * 1024 * 1024
DEFAULT_MAX_NODES = 1_000_000
DEFAULT_MAX_DEPTH = 256
DEFAULT_MAX_STRING_CHARS = 16 * 1024 * 1024
DEFAULT_MAX_NUMBER_CHARS = 1024


class StrictJSONError(ValueError):
    """Input is not strict, interoperable UTF-8 JSON."""


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise StrictJSONError("duplicate object key is forbidden")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise StrictJSONError(f"non-finite JSON number is forbidden: {value}")


def _positive_limit(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _preflight_text(
    text: str,
    label: str,
    *,
    max_depth: int,
    max_string_chars: int,
) -> None:
    """Bound nesting and source string tokens before the JSON decoder allocates."""

    depth = 0
    in_string = False
    escaped = False
    string_chars = 0
    for character in text:
        if in_string:
            if escaped:
                escaped = False
                string_chars += 1
            elif character == "\\":
                escaped = True
                string_chars += 1
            elif character == '"':
                in_string = False
            else:
                string_chars += 1
            if string_chars > max_string_chars:
                raise StrictJSONError(f"{label}: maximum JSON string length exceeded")
            continue
        if character == '"':
            in_string = True
            string_chars = 0
        elif character in "[{":
            depth += 1
            if depth > max_depth:
                raise StrictJSONError(f"{label}: maximum JSON nesting depth exceeded")
        elif character in "]}":
            depth -= 1


def loads_value(
    raw: bytes,
    label: str = "JSON input",
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_nodes: int = DEFAULT_MAX_NODES,
    max_depth: int = DEFAULT_MAX_DEPTH,
    max_string_chars: int = DEFAULT_MAX_STRING_CHARS,
    max_number_chars: int = DEFAULT_MAX_NUMBER_CHARS,
) -> Any:
    """Parse bounded exact bytes as strict, interoperable UTF-8 JSON.

    All limits are mandatory positive integers.  Callers may lower them for a
    narrower interface, while the defaults keep legacy call sites explicitly
    bounded without changing their two-positional-argument API.
    """

    max_bytes = _positive_limit(max_bytes, "max_bytes")
    max_nodes = _positive_limit(max_nodes, "max_nodes")
    max_depth = _positive_limit(max_depth, "max_depth")
    max_string_chars = _positive_limit(max_string_chars, "max_string_chars")
    max_number_chars = _positive_limit(max_number_chars, "max_number_chars")
    if not isinstance(raw, bytes):
        raise TypeError("raw JSON input must be bytes")
    if len(raw) > max_bytes:
        raise StrictJSONError(f"{label}: maximum JSON byte length exceeded")

    if raw.startswith(b"\xef\xbb\xbf"):
        raise StrictJSONError(f"{label}: UTF-8 BOM is forbidden")
    try:
        text = raw.decode("utf-8", errors="strict")
        _preflight_text(
            text,
            label,
            max_depth=max_depth,
            max_string_chars=max_string_chars,
        )

        def parse_integer(token: str) -> int:
            if len(token) > max_number_chars:
                raise StrictJSONError(f"{label}: maximum JSON number length exceeded")
            return int(token)

        def parse_float(token: str) -> float:
            if len(token) > max_number_chars:
                raise StrictJSONError(f"{label}: maximum JSON number length exceeded")
            value = float(token)
            if not math.isfinite(value):
                raise StrictJSONError(f"{label}: non-finite JSON number is forbidden")
            return value

        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_json_constant,
            parse_int=parse_integer,
            parse_float=parse_float,
        )
    except StrictJSONError:
        raise
    except UnicodeDecodeError as exc:
        raise StrictJSONError(f"{label}: input is not valid UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise StrictJSONError(
            f"{label}: invalid JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc
    except RecursionError as exc:
        raise StrictJSONError(f"{label}: maximum JSON nesting depth exceeded") from exc
    except MemoryError as exc:
        raise StrictJSONError(f"{label}: JSON resource limit exceeded") from exc
    try:
        pending: list[tuple[object, int]] = [(value, 0)]
        node_count = 0
        while pending:
            item, container_depth = pending.pop()
            node_count += 1
            if node_count > max_nodes:
                raise StrictJSONError(f"{label}: maximum JSON node count exceeded")
            if isinstance(item, dict):
                for key, child in item.items():
                    node_count += 1
                    if node_count > max_nodes:
                        raise StrictJSONError(
                            f"{label}: maximum JSON node count exceeded"
                        )
                    if len(key) > max_string_chars:
                        raise StrictJSONError(
                            f"{label}: maximum JSON string length exceeded"
                        )
                    if any(0xD800 <= ord(character) <= 0xDFFF for character in key):
                        raise StrictJSONError(
                            f"{label}: unpaired UTF-16 surrogate is forbidden"
                        )
                    pending.append((child, container_depth + 1))
            elif isinstance(item, list):
                pending.extend((child, container_depth + 1) for child in item)
            elif isinstance(item, str):
                if len(item) > max_string_chars:
                    raise StrictJSONError(
                        f"{label}: maximum JSON string length exceeded"
                    )
                if any(0xD800 <= ord(character) <= 0xDFFF for character in item):
                    raise StrictJSONError(
                        f"{label}: unpaired UTF-16 surrogate is forbidden"
                    )
    except MemoryError as exc:
        raise StrictJSONError(f"{label}: JSON resource limit exceeded") from exc
    return value


def loads_object(
    raw: bytes, label: str = "JSON input", **limits: int
) -> dict[str, Any]:
    """Parse a strict UTF-8 JSON object."""

    value = loads_value(raw, label, **limits)
    if not isinstance(value, dict):
        raise StrictJSONError(f"{label}: JSON root must be an object")
    return value


def loads_array(
    raw: bytes, label: str = "JSON input", **limits: int
) -> list[Any]:
    """Parse a strict UTF-8 JSON array."""

    value = loads_value(raw, label, **limits)
    if not isinstance(value, list):
        raise StrictJSONError(f"{label}: JSON root must be an array")
    return value


def read_bytes_bounded(
    path: Path | str,
    label: str | None = None,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> bytes:
    """Read one regular non-symlink file without allocating beyond its cap."""

    maximum = _positive_limit(max_bytes, "max_bytes")
    selected = Path(path)
    display = label or selected.name or "JSON input"
    descriptor: int | None = None
    try:
        descriptor = os.open(
            selected,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
        )
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise StrictJSONError(f"{display}: JSON input must be a regular file")
        if before.st_size > maximum:
            raise StrictJSONError(f"{display}: maximum JSON byte length exceeded")
        with os.fdopen(descriptor, "rb", closefd=True) as handle:
            descriptor = None
            raw = handle.read(maximum + 1)
            after = os.fstat(handle.fileno())
        if len(raw) > maximum:
            raise StrictJSONError(f"{display}: maximum JSON byte length exceeded")
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise StrictJSONError(f"{display}: JSON input changed while being read")
        return raw
    except StrictJSONError:
        raise
    except OSError as exc:
        raise StrictJSONError(
            f"{display}: JSON input is unavailable or unsafe ({exc.__class__.__name__})"
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def load_value(
    path: Path | str,
    label: str | None = None,
    **limits: int,
) -> Any:
    """Bounded path-level counterpart to :func:`loads_value`."""

    maximum = limits.get("max_bytes", DEFAULT_MAX_BYTES)
    display = label or Path(path).name or "JSON input"
    raw = read_bytes_bounded(path, display, max_bytes=maximum)
    return loads_value(raw, display, **limits)


def load_object(
    path: Path | str,
    label: str | None = None,
    **limits: int,
) -> dict[str, Any]:
    """Read and parse a bounded strict JSON object from a regular file."""

    value = load_value(path, label, **limits)
    if not isinstance(value, dict):
        display = label or Path(path).name or "JSON input"
        raise StrictJSONError(f"{display}: JSON root must be an object")
    return value


def load_array(
    path: Path | str,
    label: str | None = None,
    **limits: int,
) -> list[Any]:
    """Read and parse a bounded strict JSON array from a regular file."""

    value = load_value(path, label, **limits)
    if not isinstance(value, list):
        display = label or Path(path).name or "JSON input"
        raise StrictJSONError(f"{display}: JSON root must be an array")
    return value
