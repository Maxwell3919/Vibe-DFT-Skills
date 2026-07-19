#!/usr/bin/env python3
"""Strict, duplicate-key-safe YAML loading for Vibe-DFT registries."""

from __future__ import annotations

import os
from pathlib import Path
import stat
from typing import Any

import yaml
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode


MAX_YAML_BYTES = 4 * 1024 * 1024
MAX_YAML_DEPTH = 64
MAX_YAML_DISTINCT_NODES = 100_000
MAX_YAML_CONTAINER_NODES = 20_000
MAX_YAML_SCALAR_NODES = 80_000
UTF8_BOM = b"\xef\xbb\xbf"


class RegistryYAMLError(ValueError):
    """Stable registry parse error that never needs an absolute path."""

    def __init__(self, code: str, label: str, detail: str) -> None:
        self.code = code
        self.label = Path(label).name or "registry"
        self.detail = detail
        super().__init__(f"{code} {self.label}: {detail}")


class _UniqueSafeLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(
    loader: _UniqueSafeLoader,
    node: MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    if not isinstance(node, MappingNode):
        raise RegistryYAMLError("YAML_MAPPING_EXPECTED", "registry", "mapping node required")
    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise RegistryYAMLError(
                "YAML_KEY_INVALID",
                "registry",
                "mapping keys must be scalar and hashable",
            ) from exc
        if duplicate:
            raise RegistryYAMLError(
                "YAML_DUPLICATE_KEY",
                "registry",
                "duplicate mapping key",
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _check_node_graph(root: Node) -> None:
    """Bound aliases and nesting before Python containers are constructed."""

    distinct: set[int] = set()
    ancestors: set[int] = set()
    container_nodes = 0
    scalar_nodes = 0

    def visit(node: Node, depth: int) -> None:
        nonlocal container_nodes, scalar_nodes
        if depth > MAX_YAML_DEPTH:
            raise RegistryYAMLError(
                "YAML_LIMIT_DEPTH", "registry", "maximum nesting depth exceeded"
            )
        identity = id(node)
        if identity in ancestors:
            raise RegistryYAMLError(
                "YAML_GRAPH_CYCLE", "registry", "recursive aliases are forbidden"
            )
        distinct.add(identity)
        if len(distinct) > MAX_YAML_DISTINCT_NODES:
            raise RegistryYAMLError(
                "YAML_LIMIT_DISTINCT_NODES",
                "registry",
                "maximum distinct node count exceeded",
            )

        if isinstance(node, ScalarNode):
            scalar_nodes += 1
            if scalar_nodes > MAX_YAML_SCALAR_NODES:
                raise RegistryYAMLError(
                    "YAML_LIMIT_SCALAR_NODES",
                    "registry",
                    "maximum scalar node count exceeded",
                )
            return
        if isinstance(node, MappingNode):
            container_nodes += 1
            children = (child for pair in node.value for child in pair)
        elif isinstance(node, SequenceNode):
            container_nodes += 1
            children = iter(node.value)
        else:
            raise RegistryYAMLError(
                "YAML_NODE_INVALID", "registry", "unsupported YAML node kind"
            )
        if container_nodes > MAX_YAML_CONTAINER_NODES:
            raise RegistryYAMLError(
                "YAML_LIMIT_CONTAINER_NODES",
                "registry",
                "maximum container node count exceeded",
            )

        ancestors.add(identity)
        try:
            for child in children:
                visit(child, depth + 1)
        finally:
            ancestors.remove(identity)

    visit(root, 1)


def _effective_max_bytes(max_bytes: int, label: str) -> int:
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes <= 0:
        raise RegistryYAMLError(
            "YAML_LIMIT_INVALID", label, "max_bytes must be a positive integer"
        )
    return min(max_bytes, MAX_YAML_BYTES)


def loads_yaml_strict(text: str, label: str = "registry") -> dict[str, Any]:
    """Load a mapping-only YAML document with stable fail-closed errors."""

    safe_label = Path(label).name or "registry"
    if not isinstance(text, str):
        raise RegistryYAMLError("YAML_TEXT_INVALID", safe_label, "expected UTF-8 text")
    if text.startswith("\ufeff"):
        raise RegistryYAMLError(
            "YAML_BOM_FORBIDDEN", safe_label, "UTF-8 BOM is not permitted"
        )
    try:
        encoded_size = len(text.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise RegistryYAMLError(
            "YAML_ENCODING_INVALID", safe_label, "expected strict UTF-8"
        ) from exc
    if encoded_size > MAX_YAML_BYTES:
        raise RegistryYAMLError(
            "YAML_SIZE_LIMIT", safe_label, "maximum YAML byte size exceeded"
        )
    loader: _UniqueSafeLoader | None = None
    try:
        loader = _UniqueSafeLoader(text)
        node = loader.get_single_node()
        if node is None:
            value = None
        else:
            _check_node_graph(node)
            value = loader.construct_document(node)
    except RegistryYAMLError as exc:
        raise RegistryYAMLError(exc.code, safe_label, exc.detail) from None
    except yaml.constructor.ConstructorError as exc:
        raise RegistryYAMLError("YAML_UNSAFE_TAG", safe_label, "unsupported or unsafe YAML tag") from exc
    except RecursionError as exc:
        raise RegistryYAMLError(
            "YAML_LIMIT_DEPTH", safe_label, "maximum nesting depth exceeded"
        ) from exc
    except MemoryError as exc:
        raise RegistryYAMLError(
            "YAML_RESOURCE_LIMIT", safe_label, "YAML resource limit exceeded"
        ) from exc
    except yaml.YAMLError as exc:
        problem = getattr(exc, "problem", None)
        detail = str(problem) if problem else "invalid YAML syntax"
        raise RegistryYAMLError("YAML_INVALID", safe_label, detail) from exc
    finally:
        if loader is not None:
            loader.dispose()
    if not isinstance(value, dict):
        raise RegistryYAMLError("YAML_ROOT_NOT_MAPPING", safe_label, "document root must be a mapping")
    return value


def loads_yaml_bytes_strict(
    raw: bytes,
    label: str = "registry",
    *,
    max_bytes: int = MAX_YAML_BYTES,
) -> dict[str, Any]:
    """Decode bounded BOM-free UTF-8 bytes and use the canonical strict loader."""

    safe_label = Path(label).name or "registry"
    if not isinstance(raw, bytes):
        raise RegistryYAMLError("YAML_BYTES_INVALID", safe_label, "expected bytes")
    effective_limit = _effective_max_bytes(max_bytes, safe_label)
    if len(raw) > effective_limit:
        raise RegistryYAMLError(
            "YAML_SIZE_LIMIT", safe_label, "maximum YAML byte size exceeded"
        )
    if raw.startswith(UTF8_BOM):
        raise RegistryYAMLError(
            "YAML_BOM_FORBIDDEN", safe_label, "UTF-8 BOM is not permitted"
        )
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RegistryYAMLError(
            "YAML_ENCODING_INVALID", safe_label, "expected strict UTF-8"
        ) from exc
    return loads_yaml_strict(text, safe_label)


def load_yaml_strict(
    path: Path,
    label: str | None = None,
    *,
    max_bytes: int = MAX_YAML_BYTES,
) -> dict[str, Any]:
    """Read UTF-8 YAML without exposing host-specific absolute paths in errors."""

    value, _raw = load_yaml_strict_with_raw(
        path,
        label,
        max_bytes=max_bytes,
    )
    return value


def load_yaml_strict_with_raw(
    path: Path,
    label: str | None = None,
    *,
    max_bytes: int = MAX_YAML_BYTES,
) -> tuple[dict[str, Any], bytes]:
    """Return parsed data and the exact bounded bytes used for that parse."""

    safe_label = Path(label).name if label else path.name
    effective_limit = _effective_max_bytes(max_bytes, safe_label)
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError as exc:
        raise RegistryYAMLError("YAML_UNREADABLE", safe_label, exc.__class__.__name__) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise RegistryYAMLError("YAML_NOT_REGULAR", safe_label, "expected a regular file")
        if before.st_nlink != 1:
            raise RegistryYAMLError("YAML_HARDLINK_FORBIDDEN", safe_label, "hard links are forbidden")
        if before.st_size > effective_limit:
            raise RegistryYAMLError(
                "YAML_SIZE_LIMIT", safe_label, "maximum YAML byte size exceeded"
            )
        chunks: list[bytes] = []
        remaining = effective_limit + 1
        while remaining:
            block = os.read(descriptor, min(1024 * 1024, remaining))
            if not block:
                break
            chunks.append(block)
            remaining -= len(block)
        raw = b"".join(chunks)
        after = os.fstat(descriptor)
        if len(raw) > effective_limit:
            raise RegistryYAMLError(
                "YAML_SIZE_LIMIT", safe_label, "maximum YAML byte size exceeded"
            )
        before_identity = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        after_identity = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        if before_identity != after_identity or len(raw) != before.st_size:
            raise RegistryYAMLError(
                "YAML_CHANGED_DURING_READ",
                safe_label,
                "file changed while it was read",
            )
    except RegistryYAMLError:
        raise
    except OSError as exc:
        raise RegistryYAMLError("YAML_UNREADABLE", safe_label, exc.__class__.__name__) from exc
    finally:
        os.close(descriptor)
    return loads_yaml_bytes_strict(raw, safe_label, max_bytes=max_bytes), raw
