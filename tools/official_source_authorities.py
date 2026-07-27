#!/usr/bin/env python3
"""Validate and project canonical official-source technical authority data."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import ipaddress
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
from typing import Any, Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit

from registry_yaml import load_yaml_strict
import strict_json


SCHEMA_VERSION = "1.0"
IDENTIFIER = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HOST = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")
UTC_TIMESTAMP = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
TECHNICAL_ENTRY_FIELDS = {
    "lifecycle",
    "provider_class",
    "provider_id",
    "allowed_https_origins",
    "version_policy",
    "content_policy",
    "content_identity_policy",
    "canonical_snapshot",
}
PROVIDER_CLASSES = {
    "software",
    "standard",
    "platform",
    "repository",
    "model-artifact",
    "dataset",
    "publisher",
}
VERSION_POLICY_FIELDS = {
    "allowed_scopes",
    "registered_scopes",
}
VERSION_SCOPE_FIELDS = {
    "scope",
    "exact_version",
    "minimum_version",
    "maximum_version",
    "release_series",
}
VERSION_SCOPES = {
    "exact",
    "range",
    "release-series",
    "latest-at-retrieval",
    "unversioned",
}
CONTENT_POLICY_FIELDS = {
    "source_kinds",
    "allowed_path_prefixes",
    "query_policy",
    "allowed_query_urls",
    "fragment_policy",
    "resolution_mode",
}
CONTENT_IDENTITY_POLICY_FIELDS = {"mode", "unpinned_action"}
CONTENT_IDENTITY_MODES = {
    "platform-adapter-only",
    "canonical-pinned-snapshot-or-platform-adapter",
    "canonical-pinned-open-snapshot-or-platform-adapter",
    "unresolved",
}
CANONICAL_SNAPSHOT_FIELDS = {
    "snapshot_id",
    "manifest_path",
    "manifest_raw_sha256",
    "artifact_basis",
}
CP2K_MANIFEST_FIELDS = {
    "converter",
    "curated_topic_count",
    "genindex_page_count",
    "index_page_count",
    "index_sha256",
    "internal_link_count",
    "linked_page_count",
    "manual_index_sha256",
    "manual_branch",
    "manual_version",
    "mirrored_page_count",
    "mirrored_topic_count",
    "pages",
    "registry_sha256",
    "retrieved_utc",
    "schema_version",
}
CP2K_PAGE_FIELDS = {
    "conversion_quality",
    "curated_topic",
    "indexed",
    "path",
    "raw_bytes",
    "raw_sha256",
    "snapshot_bytes",
    "snapshot_sha256",
    "source_path",
    "source_url",
}
CP2K_CONVERTER_FIELDS = {
    "adapter_path",
    "adapter_schema_version",
    "adapter_sha256",
    "dependencies",
    "expected_upstream_commit",
    "git_commit",
    "project_name",
    "project_version",
    "upstream_url",
}
CP2K_CONVERTER_DEPENDENCIES = {
    "jsdom",
    "turndown",
    "turndown-plugin-gfm",
}
CP2K_CONVERSION_QUALITY_FIELDS = {
    "anchor_count",
    "internal_link_count",
    "markdown_token_count",
    "max_line_chars",
    "non_ascii_characters_preserved",
    "replacement_characters",
    "source_non_ascii_chars",
    "source_alphanumeric_character_count",
    "source_text_chars",
    "source_text_sha256",
    "source_token_count",
    "sphinx_private_header_glyphs",
    "status",
    "token_sequence_preserved",
}
HTML2MD_UPSTREAM = "https://github.com/helloworld-Co/html2md"
HTML2MD_COMMIT = "ca08965af93e6565806a79087868daa439565ffc"
CP2K_INDEX_FIELDS = {
    "genindex_page_count",
    "linked_page_count",
    "manual_branch",
    "manual_version",
    "page_count",
    "pages",
    "schema_version",
    "source_sha256",
    "source_url",
}
SOURCE_KINDS = {
    "official-manual",
    "official-reference",
    "official-release-notes",
    "official-repository",
    "official-dataset",
    "official-api-metadata",
}
SHA256 = re.compile(r"^[a-f0-9]{64}$")
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
MAX_SNAPSHOT_BYTES = 16 * 1024 * 1024
MAX_SNAPSHOT_COUNT = 4096
MAX_TOTAL_SNAPSHOT_BYTES = 512 * 1024 * 1024


def cp2k_source_id(source_path: str) -> str:
    """Return the stable corpus ID for one canonical CP2K index path."""

    return (
        "cp2k-page-"
        + hashlib.sha256(source_path.encode("utf-8")).hexdigest()[:32]
    )


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def registry_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / "registry" / "official-source-authorities.yaml"


def load_registry(path: Path | None = None) -> dict[str, Any]:
    return load_yaml_strict(path or registry_path(), "official-source-authorities.yaml")


def _string_list(
    value: object,
    location: str,
    failures: list[str],
    *,
    allowed: set[str] | None = None,
    nonempty: bool = False,
) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        failures.append(f"{location}: expected {'a nonempty ' if nonempty else ''}string list")
        return []
    if not all(isinstance(item, str) and item for item in value):
        failures.append(f"{location}: expected nonempty string values")
        return []
    if len(value) != len(set(value)):
        failures.append(f"{location}: duplicate values are forbidden")
    if allowed is not None:
        for index, item in enumerate(value):
            if item not in allowed:
                failures.append(f"{location}/{index}: unsupported value")
    return value


def _https_origin(value: object) -> bool:
    return _canonical_https_parts(value, require_path=False) is not None


def _canonical_https_parts(
    value: object,
    *,
    require_path: bool,
) -> tuple[str, str] | None:
    """Return canonical origin/path while rejecting URL parser ambiguities."""

    if not isinstance(value, str) or "%" in value or "\\" in value:
        return None
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return None
    hostname = parsed.hostname
    if (
        parsed.scheme != "https"
        or not isinstance(hostname, str)
        or HOST.fullmatch(hostname) is None
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 443}
        or parsed.query
        or parsed.fragment
    ):
        return None
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        return None
    if hostname == "localhost" or hostname.endswith(".localhost"):
        return None
    origin = f"https://{hostname}" + (":443" if port == 443 else "")
    path = parsed.path
    if value != origin + path:
        return None
    if require_path:
        if not path.startswith("/") or not path or "//" in path:
            return None
    elif path:
        return None
    if any(segment in {".", ".."} for segment in path.split("/")):
        return None
    return origin, path


def _url_allowed(url: str, origins: list[str], prefixes: list[str]) -> bool:
    parts = _canonical_https_parts(url, require_path=True)
    if parts is None:
        return False
    origin, path = parts
    return origin in origins and any(path.startswith(prefix) for prefix in prefixes)


def _canonical_query_https_parts(
    value: object,
) -> tuple[str, str] | None:
    """Return canonical origin/path for one exact query-bearing HTTPS URL."""

    if not isinstance(value, str) or "#" in value or "?" not in value:
        return None
    base, separator, raw_query = value.partition("?")
    if separator != "?" or not raw_query:
        return None
    base_parts = _canonical_https_parts(base, require_path=True)
    if base_parts is None:
        return None
    try:
        parsed = urlsplit(value)
        pairs = parse_qsl(
            parsed.query,
            keep_blank_values=True,
            strict_parsing=True,
        )
    except ValueError:
        return None
    if (
        not pairs
        or parsed.fragment
        or parsed.query != raw_query
        or any(not key for key, _ in pairs)
    ):
        return None
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        return None
    canonical_query = urlencode(pairs)
    if canonical_query != raw_query or value != f"{base}?{canonical_query}":
        return None
    return base_parts


def _valid_version_scope(value: object, location: str, failures: list[str]) -> bool:
    if not isinstance(value, dict) or set(value) != VERSION_SCOPE_FIELDS:
        failures.append(f"{location}: expected exact version-scope fields")
        return False
    scope = value.get("scope")
    if scope not in VERSION_SCOPES:
        failures.append(f"{location}/scope: unsupported scope")
        return False
    for field in VERSION_SCOPE_FIELDS - {"scope"}:
        item = value.get(field)
        if item is not None and (not isinstance(item, str) or not item.strip()):
            failures.append(f"{location}/{field}: expected null or a nonempty string")
    populated = {field for field in VERSION_SCOPE_FIELDS - {"scope"} if value.get(field) is not None}
    expected = {
        "exact": {"exact_version"},
        "range": {field for field in ("minimum_version", "maximum_version") if value.get(field) is not None},
        "release-series": {"release_series"},
        "latest-at-retrieval": set(),
        "unversioned": set(),
    }[scope]
    if scope == "range" and not expected:
        failures.append(f"{location}: range requires a minimum or maximum version")
    elif populated != expected:
        failures.append(f"{location}: fields do not match scope {scope!r}")
    return True


def _valid_timestamp(value: object) -> bool:
    if not isinstance(value, str) or UTC_TIMESTAMP.fullmatch(value) is None:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo == timezone.utc


def _valid_utc_timestamp(value: object) -> bool:
    """Accept a complete ISO timestamp only when its actual offset is UTC."""

    if not isinstance(value, str) or "T" not in value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed)


def _read_regular_file(
    root: Path,
    relative_text: object,
    *,
    maximum_bytes: int,
) -> tuple[bytes | None, str | None]:
    if (
        not isinstance(relative_text, str)
        or not relative_text
        or "%" in relative_text
        or "\\" in relative_text
    ):
        return None, "expected a nonempty repository-relative path"
    relative = PurePosixPath(relative_text)
    if (
        relative.is_absolute()
        or any(part in {"", ".", ".."} for part in relative_text.split("/"))
    ):
        return None, "expected a safe repository-relative path"
    current = root
    try:
        for part in relative.parts[:-1]:
            current = current / part
            if stat.S_ISLNK(os.lstat(current).st_mode):
                return None, "parent symlinks are forbidden"
        path = root.joinpath(*relative.parts)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
    except OSError as exc:
        return None, f"file is unavailable ({exc.__class__.__name__})"
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            return None, "expected a regular file"
        if before.st_nlink != 1:
            return None, "hard-linked files are forbidden"
        if before.st_size > maximum_bytes:
            return None, "file exceeds the byte limit"
        chunks: list[bytes] = []
        remaining = maximum_bytes + 1
        while remaining:
            block = os.read(descriptor, min(1024 * 1024, remaining))
            if not block:
                break
            chunks.append(block)
            remaining -= len(block)
        raw = b"".join(chunks)
        after = os.fstat(descriptor)
        if len(raw) > maximum_bytes:
            return None, "file exceeds the byte limit"
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        )
        if identity_before != identity_after or len(raw) != before.st_size:
            return None, "file changed while it was read"
        return raw, None
    except OSError as exc:
        return None, f"file is unreadable ({exc.__class__.__name__})"
    finally:
        os.close(descriptor)


def _load_json_object_strict(raw: bytes) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return (
            strict_json.loads_object(
                raw,
                "canonical snapshot manifest",
                max_bytes=MAX_MANIFEST_BYTES,
                max_nodes=250_000,
                max_depth=64,
                max_string_chars=1024 * 1024,
                max_number_chars=256,
            ),
            None,
        )
    except strict_json.StrictJSONError as exc:
        return None, str(exc)


def _canonical_snapshot_projection(
    authority_id: str,
    entry: dict[str, Any],
    root: Path | None,
    expected_skill: str | None,
    *,
    externalized_receipts: Mapping[str, Mapping[str, object]] | None = None,
    used_externalized_paths: set[str] | None = None,
) -> tuple[list[str], dict[str, Any] | None]:
    location = f"authorities/{authority_id}/canonical_snapshot"
    canonical = entry.get("canonical_snapshot")
    if canonical is None:
        return [], None
    failures: list[str] = []
    if not isinstance(canonical, dict) or set(canonical) != CANONICAL_SNAPSHOT_FIELDS:
        return [f"{location}: expected fields {sorted(CANONICAL_SNAPSHOT_FIELDS)}"], None
    snapshot_id = canonical.get("snapshot_id")
    if not isinstance(snapshot_id, str) or IDENTIFIER.fullmatch(snapshot_id) is None:
        failures.append(f"{location}/snapshot_id: invalid snapshot identifier")
    manifest_path = canonical.get("manifest_path")
    relative = PurePosixPath(manifest_path) if isinstance(manifest_path, str) else None
    if (
        relative is None
        or relative.is_absolute()
        or "%" in manifest_path
        or "\\" in manifest_path
        or any(part in {"", ".", ".."} for part in manifest_path.split("/"))
        or ".." in relative.parts
        or len(relative.parts) < 4
        or relative.parts[0] != "skills"
        or relative.name != "manifest.json"
    ):
        failures.append(f"{location}/manifest_path: expected a safe Skill-local manifest.json")
    elif expected_skill is None:
        failures.append(f"{location}/manifest_path: provider Skill ownership is unresolved")
    elif relative.parts[1] != expected_skill:
        failures.append(f"{location}/manifest_path: manifest must belong to the provider Skill")
    declared_manifest_hash = canonical.get("manifest_raw_sha256")
    if not isinstance(declared_manifest_hash, str) or SHA256.fullmatch(declared_manifest_hash) is None:
        failures.append(f"{location}/manifest_raw_sha256: expected a SHA-256")
    artifact_basis = canonical.get("artifact_basis")
    if artifact_basis not in {
        "derived-snapshot-file-exact-bytes",
        "external-cache-manifest-receipt-exact-bytes",
    }:
        failures.append(f"{location}/artifact_basis: unsupported artifact basis")
    receipt_only = (
        artifact_basis == "external-cache-manifest-receipt-exact-bytes"
    )
    if root is None or relative is None or failures:
        if root is None:
            failures.append(f"{location}: source_root is required to verify a canonical snapshot")
        return failures, None

    manifest_raw, read_error = _read_regular_file(
        root,
        relative.as_posix(),
        maximum_bytes=MAX_MANIFEST_BYTES,
    )
    if read_error is not None or manifest_raw is None:
        receipt = (
            externalized_receipts.get(relative.as_posix())
            if externalized_receipts is not None
            else None
        )
        index_path = (relative.parent / "index.json").as_posix()
        index_receipt = (
            externalized_receipts.get(index_path)
            if externalized_receipts is not None
            else None
        )
        if (
            read_error == "file is unavailable (FileNotFoundError)"
            and isinstance(receipt, Mapping)
            and set(receipt) == {"path", "sha256", "size"}
            and receipt.get("path") == relative.as_posix()
            and receipt.get("sha256") == declared_manifest_hash
            and isinstance(receipt.get("size"), int)
            and not isinstance(receipt.get("size"), bool)
            and 0 <= receipt["size"] <= MAX_MANIFEST_BYTES
            and (
                index_receipt is None
                or (
                    isinstance(index_receipt, Mapping)
                    and set(index_receipt) == {"path", "sha256", "size"}
                    and index_receipt.get("path") == index_path
                    and isinstance(index_receipt.get("sha256"), str)
                    and SHA256.fullmatch(index_receipt["sha256"]) is not None
                    and isinstance(index_receipt.get("size"), int)
                    and not isinstance(index_receipt.get("size"), bool)
                    and 0 <= index_receipt["size"] <= MAX_MANIFEST_BYTES
                )
            )
        ):
            if used_externalized_paths is not None:
                used_externalized_paths.add(relative.as_posix())
                if isinstance(index_receipt, Mapping):
                    used_externalized_paths.add(index_path)
            return [], {
                "snapshot_id": snapshot_id,
                "manifest_raw_sha256": declared_manifest_hash,
                "index_raw_sha256": (
                    index_receipt["sha256"]
                    if isinstance(index_receipt, Mapping)
                    else None
                ),
                "integrity_verified": False,
                "upstream_source_count": None,
                "upstream_universe_complete": False,
                "upstream_sources_by_id": {},
                "curated_source_count": None,
                "sources_by_id": {},
                "portable_externalized": True,
            }
        failures.append(f"{location}/manifest_path: {read_error}")
        return failures, None
    actual_manifest_hash = hashlib.sha256(manifest_raw).hexdigest()
    if actual_manifest_hash != declared_manifest_hash:
        failures.append(f"{location}/manifest_raw_sha256: declared digest does not match exact bytes")
        return failures, None
    manifest, manifest_error = _load_json_object_strict(manifest_raw)
    if manifest_error is not None or manifest is None:
        failures.append(f"{location}/manifest_path: {manifest_error}")
        return failures, None
    if set(manifest) != CP2K_MANIFEST_FIELDS:
        failures.append(f"{location}/manifest_path: unsupported manifest fields")
        return failures, None
    if manifest.get("schema_version") != "2.0":
        failures.append(f"{location}/manifest_path: expected schema_version '2.0'")
    manual_branch = manifest.get("manual_branch")
    authority_prefixes = entry.get("content_policy", {}).get("allowed_path_prefixes", [])
    if (
        not isinstance(manual_branch, str)
        or not manual_branch
        or not isinstance(authority_prefixes, list)
        or not any(prefix == f"/{manual_branch}/" for prefix in authority_prefixes)
    ):
        failures.append(f"{location}/manifest_path: manual_branch does not match authority path")
    for field in ("index_sha256", "registry_sha256"):
        if not isinstance(manifest.get(field), str) or SHA256.fullmatch(manifest[field]) is None:
            failures.append(f"{location}/manifest_path: invalid {field}")
    if not _valid_utc_timestamp(manifest.get("retrieved_utc")):
        failures.append(f"{location}/manifest_path: invalid retrieved_utc")
    converter = manifest.get("converter")
    converter_location = f"{location}/manifest/converter"
    if not isinstance(converter, dict) or set(converter) != CP2K_CONVERTER_FIELDS:
        failures.append(f"{converter_location}: unsupported converter fields")
    else:
        if (
            converter.get("adapter_path") != "scripts/html2md_adapter.js"
            or converter.get("adapter_schema_version") != "1.0"
            or converter.get("project_name") != "hello-html2md"
            or converter.get("upstream_url") != HTML2MD_UPSTREAM
            or converter.get("git_commit") != HTML2MD_COMMIT
            or converter.get("expected_upstream_commit") != HTML2MD_COMMIT
            or not isinstance(converter.get("project_version"), str)
            or not converter["project_version"]
        ):
            failures.append(f"{converter_location}: unsupported pinned html2md identity")
        adapter_sha256 = converter.get("adapter_sha256")
        if (
            not isinstance(adapter_sha256, str)
            or SHA256.fullmatch(adapter_sha256) is None
        ):
            failures.append(f"{converter_location}/adapter_sha256: expected a SHA-256")
        dependencies = converter.get("dependencies")
        if (
            not isinstance(dependencies, dict)
            or set(dependencies) != CP2K_CONVERTER_DEPENDENCIES
            or not all(
                isinstance(value, str) and value
                for value in dependencies.values()
            )
        ):
            failures.append(f"{converter_location}/dependencies: incomplete identity")
        adapter_relative = PurePosixPath(
            "skills",
            expected_skill or "",
            "scripts",
            "html2md_adapter.js",
        )
        adapter_raw, adapter_error = _read_regular_file(
            root,
            adapter_relative.as_posix(),
            maximum_bytes=MAX_MANIFEST_BYTES,
        )
        if adapter_error is not None or adapter_raw is None:
            failures.append(f"{converter_location}/adapter_path: {adapter_error}")
        elif hashlib.sha256(adapter_raw).hexdigest() != adapter_sha256:
            failures.append(
                f"{converter_location}/adapter_sha256: does not match exact adapter bytes"
            )
    version_scopes = entry.get("version_policy", {}).get("registered_scopes", [])
    if not isinstance(version_scopes, list) or len(version_scopes) != 1:
        failures.append(f"{location}: canonical snapshots require exactly one registered version scope")
        version_scope = None
    else:
        version_scope = version_scopes[0]
        scope = version_scope.get("scope") if isinstance(version_scope, dict) else None
        expected_version = (
            version_scope.get("exact_version")
            if scope == "exact"
            else version_scope.get("release_series") if scope == "release-series" else None
        )
        if expected_version is None or manifest.get("manual_version") != expected_version:
            failures.append(f"{location}/manifest_path: manual_version does not match authority version")
    pages = manifest.get("pages")
    if not isinstance(pages, dict) or not pages:
        failures.append(f"{location}/manifest_path: pages must be a nonempty mapping")
        pages = {}
    elif len(pages) > MAX_SNAPSHOT_COUNT:
        failures.append(f"{location}/manifest_path: pages exceed the snapshot count limit")
        return failures, None
    if manifest.get("mirrored_topic_count") != len(pages):
        failures.append(f"{location}/manifest_path: mirrored_topic_count does not match pages")
    if manifest.get("mirrored_page_count") != len(pages):
        failures.append(f"{location}/manifest_path: mirrored_page_count does not match pages")
    if (
        not isinstance(manifest.get("index_page_count"), int)
        or isinstance(manifest.get("index_page_count"), bool)
        or manifest["index_page_count"] != len(pages)
    ):
        failures.append(f"{location}/manifest_path: invalid index_page_count")
    for field in ("genindex_page_count", "linked_page_count"):
        if (
            not isinstance(manifest.get(field), int)
            or isinstance(manifest.get(field), bool)
            or manifest[field] < 0
        ):
            failures.append(f"{location}/manifest_path: invalid {field}")
    if (
        isinstance(manifest.get("genindex_page_count"), int)
        and isinstance(manifest.get("linked_page_count"), int)
        and manifest["genindex_page_count"] + manifest["linked_page_count"]
        != manifest.get("index_page_count")
    ):
        failures.append(f"{location}/manifest_path: link-closure counts do not close")

    manifest_parent = relative.parent
    index_relative = manifest_parent / "index.json"
    index_raw, index_error = _read_regular_file(
        root,
        index_relative.as_posix(),
        maximum_bytes=MAX_MANIFEST_BYTES,
    )
    upstream_sources: dict[str, dict[str, Any]] = {}
    if index_error is not None or index_raw is None:
        failures.append(f"{location}/manifest_path: canonical index is unavailable ({index_error})")
    else:
        actual_index_hash = hashlib.sha256(index_raw).hexdigest()
        if manifest.get("index_sha256") != actual_index_hash:
            failures.append(
                f"{location}/manifest_path: index_sha256 does not match exact index bytes"
            )
        index, index_parse_error = _load_json_object_strict(index_raw)
        if index_parse_error is not None or index is None:
            failures.append(
                f"{location}/manifest_path: canonical index is invalid ({index_parse_error})"
            )
        elif set(index) != CP2K_INDEX_FIELDS:
            failures.append(f"{location}/manifest_path: unsupported canonical index fields")
        else:
            index_pages = index.get("pages")
            if (
                index.get("schema_version") != "2.0"
                or index.get("manual_branch") != manifest.get("manual_branch")
                or index.get("manual_version") != manifest.get("manual_version")
                or not isinstance(index_pages, list)
                or not index_pages
                or not all(isinstance(item, str) and item for item in index_pages)
                or len(index_pages) != len(set(index_pages))
                or index.get("page_count") != len(index_pages)
                or manifest.get("index_page_count") != len(index_pages)
                or index.get("genindex_page_count")
                != manifest.get("genindex_page_count")
                or index.get("linked_page_count") != manifest.get("linked_page_count")
                or index.get("genindex_page_count", 0)
                + index.get("linked_page_count", 0)
                != len(index_pages)
            ):
                failures.append(
                    f"{location}/manifest_path: canonical index does not declare one "
                    "exact complete source-path universe"
                )
            else:
                source_ids: set[str] = set()
                manual_branch_prefix = f"/{manifest['manual_branch']}/"
                for source_path in index_pages:
                    source_id = cp2k_source_id(source_path)
                    if (
                        len(source_id) > 128
                        or re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,127}", source_id)
                        is None
                        or source_id in source_ids
                        or source_path.startswith("/")
                        or "%"
                        in source_path
                        or "\\"
                        in source_path
                        or any(
                            part in {"", ".", ".."}
                            for part in source_path.split("/")
                        )
                    ):
                        failures.append(
                            f"{location}/manifest_path: canonical index contains an "
                            "invalid or colliding source path"
                        )
                        break
                    source_ids.add(source_id)
                    upstream_sources[source_id] = {
                        "canonical_url": (
                            f"https://manual.cp2k.org{manual_branch_prefix}{source_path}"
                        ),
                        "source_path": source_path,
                    }

    origins = entry.get("allowed_https_origins", [])
    prefixes = entry.get("content_policy", {}).get("allowed_path_prefixes", [])
    manifest_parent = relative.parent
    sources: dict[str, dict[str, Any]] = {}
    local_paths: set[str] = set()
    source_urls: set[str] = set()
    total_snapshot_bytes = 0
    for source_id, page in pages.items():
        page_location = f"{location}/manifest/pages/{source_id}"
        if not isinstance(source_id, str) or IDENTIFIER.fullmatch(source_id) is None:
            failures.append(f"{page_location}: invalid source identifier")
        if not isinstance(page, dict) or set(page) != CP2K_PAGE_FIELDS:
            failures.append(f"{page_location}: unsupported page fields")
            continue
        if page.get("indexed") is not True:
            failures.append(f"{page_location}/indexed: must be true")
        local_name = page.get("path")
        local_relative = PurePosixPath(local_name) if isinstance(local_name, str) else None
        if (
            local_relative is None
            or local_relative.is_absolute()
            or "%" in local_name
            or "\\" in local_name
            or ".." in local_relative.parts
        ):
            failures.append(f"{page_location}/path: expected one safe snapshot path")
            continue
        if local_relative.as_posix() in local_paths:
            failures.append(f"{page_location}/path: duplicate snapshot path")
        local_paths.add(local_relative.as_posix())
        source_url = page.get("source_url")
        if not isinstance(source_url, str) or not _url_allowed(source_url, origins, prefixes):
            failures.append(f"{page_location}/source_url: URL is outside authority locator policy")
        elif source_url in source_urls:
            failures.append(f"{page_location}/source_url: duplicate canonical URL")
        source_urls.add(source_url if isinstance(source_url, str) else "")
        source_path = page.get("source_path")
        if (
            not isinstance(source_path, str)
            or not source_path
            or source_path.startswith("/")
            or "%" in source_path
            or "\\" in source_path
            or any(part in {"", ".", ".."} for part in source_path.split("/"))
        ):
            failures.append(f"{page_location}/source_path: invalid source path")
        elif isinstance(source_url, str) and not urlsplit(source_url).path.endswith("/" + source_path):
            failures.append(f"{page_location}/source_path: does not match canonical URL")
        if isinstance(source_path, str) and source_id != cp2k_source_id(source_path):
            failures.append(f"{page_location}: source ID does not match source path")
        for field in ("raw_sha256", "snapshot_sha256"):
            if not isinstance(page.get(field), str) or SHA256.fullmatch(page[field]) is None:
                failures.append(f"{page_location}/{field}: expected a SHA-256")
        for field in ("raw_bytes", "snapshot_bytes"):
            if not isinstance(page.get(field), int) or isinstance(page.get(field), bool) or page[field] < 0:
                failures.append(f"{page_location}/{field}: expected a nonnegative integer")
        declared_snapshot_bytes = page.get("snapshot_bytes")
        if isinstance(declared_snapshot_bytes, int) and not isinstance(declared_snapshot_bytes, bool):
            if declared_snapshot_bytes > MAX_SNAPSHOT_BYTES:
                failures.append(f"{page_location}/snapshot_bytes: exceeds the per-file byte limit")
                continue
            total_snapshot_bytes += declared_snapshot_bytes
            if total_snapshot_bytes > MAX_TOTAL_SNAPSHOT_BYTES:
                failures.append(f"{location}/manifest_path: snapshots exceed the total byte limit")
                return failures, None
        snapshot_relative = (manifest_parent / local_relative).as_posix()
        snapshot_raw: bytes | None = None
        actual_snapshot_hash = page.get("snapshot_sha256")
        actual_snapshot_bytes = page.get("snapshot_bytes")
        if not receipt_only:
            snapshot_raw, snapshot_error = _read_regular_file(
                root,
                snapshot_relative,
                maximum_bytes=MAX_SNAPSHOT_BYTES,
            )
            if snapshot_error is not None or snapshot_raw is None:
                failures.append(f"{page_location}/path: {snapshot_error}")
                continue
            actual_snapshot_hash = hashlib.sha256(snapshot_raw).hexdigest()
            actual_snapshot_bytes = len(snapshot_raw)
            if page.get("snapshot_sha256") != actual_snapshot_hash:
                failures.append(f"{page_location}/snapshot_sha256: does not match exact snapshot bytes")
            if page.get("snapshot_bytes") != actual_snapshot_bytes:
                failures.append(f"{page_location}/snapshot_bytes: does not match exact snapshot bytes")
        quality = page.get("conversion_quality")
        quality_location = f"{page_location}/conversion_quality"
        if (
            not isinstance(quality, dict)
            or set(quality) != CP2K_CONVERSION_QUALITY_FIELDS
        ):
            failures.append(f"{quality_location}: unsupported quality fields")
        else:
            if (
                quality.get("status") != "pass"
                or quality.get("token_sequence_preserved") is not True
                or quality.get("non_ascii_characters_preserved") is not True
                or quality.get("replacement_characters") != 0
                or quality.get("sphinx_private_header_glyphs") != 0
                or not isinstance(quality.get("source_text_sha256"), str)
                or SHA256.fullmatch(quality["source_text_sha256"]) is None
            ):
                failures.append(f"{quality_location}: positive quality gates are incomplete")
            for field in (
                "source_text_chars",
                "source_alphanumeric_character_count",
                "source_token_count",
                "source_non_ascii_chars",
                "markdown_token_count",
                "max_line_chars",
            ):
                if (
                    not isinstance(quality.get(field), int)
                    or isinstance(quality.get(field), bool)
                    or quality[field] < 0
                ):
                    failures.append(f"{quality_location}/{field}: expected a nonnegative integer")
            if (
                isinstance(quality.get("source_token_count"), int)
                and isinstance(quality.get("markdown_token_count"), int)
                and quality["markdown_token_count"] < quality["source_token_count"]
            ):
                failures.append(f"{quality_location}: Markdown token count is smaller than source")
            if snapshot_raw is not None:
                try:
                    snapshot_text = snapshot_raw.decode("utf-8", errors="strict")
                except UnicodeDecodeError:
                    failures.append(f"{quality_location}: snapshot is not valid UTF-8")
                    snapshot_text = None
                if snapshot_text is not None:
                    actual_max_line = max(
                        (len(line) for line in snapshot_text.splitlines()),
                        default=0,
                    )
                    if (
                        quality.get("max_line_chars") != actual_max_line
                        or actual_max_line > 20_000
                        or "\ufffd" in snapshot_text
                        or "\uf0c1" in snapshot_text
                    ):
                        failures.append(
                            f"{quality_location}: display-quality evidence does not "
                            "match exact snapshot bytes"
                        )
            elif quality.get("max_line_chars", 0) > 20_000:
                failures.append(
                    f"{quality_location}: recorded line length exceeds limit"
                )
        curated_topic = page.get("curated_topic")
        if (
            curated_topic is not None
            and version_scope is not None
            and isinstance(source_url, str)
        ):
            canonical_source_id = cp2k_source_id(source_path)
            if canonical_source_id not in upstream_sources:
                failures.append(
                    f"{page_location}/source_path: source path is absent from the "
                    "canonical upstream index"
                )
                continue
            sources[canonical_source_id] = {
                "canonical_url": source_url,
                "version_scope": copy.deepcopy(version_scope),
                "raw_sha256": page["raw_sha256"],
                "raw_bytes": page["raw_bytes"],
                "raw_integrity_verified": False,
                "topic_alias": curated_topic,
                "derived_snapshot": {
                    "path": snapshot_relative,
                    "sha256": actual_snapshot_hash,
                    "bytes": actual_snapshot_bytes,
                    "integrity_verified": not receipt_only,
                },
            }
    if failures:
        return failures, None
    return [], {
        "snapshot_id": snapshot_id,
        "manifest_raw_sha256": actual_manifest_hash,
        "index_raw_sha256": hashlib.sha256(index_raw).hexdigest(),
        "integrity_verified": not receipt_only,
        "upstream_source_count": len(upstream_sources),
        "upstream_universe_complete": True,
        "upstream_sources_by_id": upstream_sources,
        "curated_source_count": len(sources),
        "sources_by_id": sources,
    }


def validate_and_project_technical(
    data: object,
    *,
    software_data: dict[str, Any] | None = None,
    source_root: Path | None = None,
    externalized_receipts: Mapping[str, Mapping[str, object]] | None = None,
    used_externalized_paths: set[str] | None = None,
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    failures: list[str] = []
    if not isinstance(data, dict):
        return ["<root>: registry must be a mapping"], {}
    if set(data) != {"schema_version", "authorities"}:
        failures.append("<root>: expected schema_version and authorities only")
    if data.get("schema_version") != SCHEMA_VERSION:
        failures.append(f"schema_version: expected {SCHEMA_VERSION!r}")
    authorities = data.get("authorities")
    if not isinstance(authorities, dict) or not authorities:
        failures.append("authorities: expected a nonempty mapping")
        return failures, {}

    software_providers_by_authority_lifecycle: dict[str, list[str]] = {
        "active": [],
        "planned": [],
    }
    canonical_projections: dict[str, dict[str, Any] | None] = {}
    provider_skills: dict[str, str] = {}
    if isinstance(software_data, dict):
        active_software = software_data.get("software", {})
        if isinstance(active_software, dict):
            provider_skills.update(
                {
                    provider: specification["calculation_skill"]
                    for provider, specification in active_software.items()
                    if isinstance(specification, dict)
                    and isinstance(specification.get("calculation_skill"), str)
                }
            )
        planned_software = software_data.get("planned_software", {})
        if isinstance(planned_software, dict):
            provider_skills.update(
                {
                    provider: specification["intended_skill"]
                    for provider, specification in planned_software.items()
                    if isinstance(specification, dict)
                    and isinstance(specification.get("intended_skill"), str)
                }
            )
    for authority_id, entry in authorities.items():
        location = f"authorities/{authority_id}"
        if not isinstance(authority_id, str) or IDENTIFIER.fullmatch(authority_id) is None:
            failures.append(f"{location}: invalid authority identifier")
        if not isinstance(entry, dict):
            failures.append(f"{location}: expected a mapping")
            continue
        missing_fields = TECHNICAL_ENTRY_FIELDS - set(entry)
        if missing_fields:
            failures.append(
                f"{location}: missing technical fields {sorted(missing_fields)}"
            )
        lifecycle = entry.get("lifecycle")
        if lifecycle not in software_providers_by_authority_lifecycle:
            failures.append(f"{location}/lifecycle: expected active or planned")
            lifecycle = "planned"
        provider_class = entry.get("provider_class")
        if provider_class not in PROVIDER_CLASSES:
            failures.append(
                f"{location}/provider_class: unsupported provider class"
            )
        provider_id = entry.get("provider_id")
        if not isinstance(provider_id, str) or IDENTIFIER.fullmatch(provider_id) is None:
            failures.append(f"{location}/provider_id: invalid provider identifier")
        elif provider_class == "software":
            software_providers_by_authority_lifecycle[lifecycle].append(
                provider_id
            )

        origins = _string_list(
            entry.get("allowed_https_origins"),
            f"{location}/allowed_https_origins",
            failures,
            nonempty=lifecycle == "active",
        )
        for index, origin in enumerate(origins):
            if not _https_origin(origin):
                failures.append(f"{location}/allowed_https_origins/{index}: expected a canonical HTTPS origin")

        version = entry.get("version_policy")
        if not isinstance(version, dict) or set(version) != VERSION_POLICY_FIELDS:
            failures.append(f"{location}/version_policy: expected fields {sorted(VERSION_POLICY_FIELDS)}")
            version = {}
        allowed_scopes = _string_list(
            version.get("allowed_scopes"),
            f"{location}/version_policy/allowed_scopes",
            failures,
            allowed=VERSION_SCOPES,
            nonempty=lifecycle == "active",
        )
        registered_scopes = version.get("registered_scopes")
        if not isinstance(registered_scopes, list) or (lifecycle == "active" and not registered_scopes):
            failures.append(f"{location}/version_policy/registered_scopes: expected {'a nonempty ' if lifecycle == 'active' else ''}list")
            registered_scopes = []
        for index, scope in enumerate(registered_scopes):
            if _valid_version_scope(scope, f"{location}/version_policy/registered_scopes/{index}", failures):
                if scope["scope"] not in allowed_scopes:
                    failures.append(f"{location}/version_policy/registered_scopes/{index}: scope is not allowed")
        if len({repr(item) for item in registered_scopes}) != len(registered_scopes):
            failures.append(f"{location}/version_policy/registered_scopes: duplicate scopes are forbidden")
        content = entry.get("content_policy")
        if not isinstance(content, dict) or set(content) != CONTENT_POLICY_FIELDS:
            failures.append(f"{location}/content_policy: expected fields {sorted(CONTENT_POLICY_FIELDS)}")
            content = {}
        _string_list(
            content.get("source_kinds"),
            f"{location}/content_policy/source_kinds",
            failures,
            allowed=SOURCE_KINDS,
            nonempty=lifecycle == "active",
        )
        prefixes = _string_list(
            content.get("allowed_path_prefixes"),
            f"{location}/content_policy/allowed_path_prefixes",
            failures,
            nonempty=lifecycle == "active",
        )
        for index, prefix in enumerate(prefixes):
            if (
                not prefix.startswith("/")
                or not prefix.endswith("/")
                or "%" in prefix
                or "\\" in prefix
                or "//" in prefix
                or any(part in {".", ".."} for part in prefix.split("/"))
            ):
                failures.append(f"{location}/content_policy/allowed_path_prefixes/{index}: invalid absolute path prefix")
        query_policy = content.get("query_policy")
        if query_policy not in {"forbidden", "exact-allowlist"}:
            failures.append(
                f"{location}/content_policy/query_policy: unsupported policy"
            )
        allowed_query_urls = _string_list(
            content.get("allowed_query_urls"),
            f"{location}/content_policy/allowed_query_urls",
            failures,
            nonempty=query_policy == "exact-allowlist",
        )
        if query_policy == "forbidden" and allowed_query_urls:
            failures.append(
                f"{location}/content_policy/allowed_query_urls: forbidden query "
                "policy requires an empty list"
            )
        if allowed_query_urls != sorted(allowed_query_urls):
            failures.append(
                f"{location}/content_policy/allowed_query_urls: exact URLs must "
                "be sorted by raw URL"
            )
        for index, query_url in enumerate(allowed_query_urls):
            parts = _canonical_query_https_parts(query_url)
            if parts is None:
                failures.append(
                    f"{location}/content_policy/allowed_query_urls/{index}: "
                    "expected one canonical query-bearing HTTPS URL with unique "
                    "keys and canonical encoding"
                )
                continue
            origin, path = parts
            if origin not in origins or not any(
                path.startswith(prefix) for prefix in prefixes
            ):
                failures.append(
                    f"{location}/content_policy/allowed_query_urls/{index}: "
                    "URL is outside the authority origin/path policy"
                )
        if content.get("fragment_policy") != "forbidden":
            failures.append(f"{location}/content_policy/fragment_policy: must be forbidden")
        identity = entry.get("content_identity_policy")
        if not isinstance(identity, dict) or set(identity) != CONTENT_IDENTITY_POLICY_FIELDS:
            failures.append(
                f"{location}/content_identity_policy: expected fields "
                f"{sorted(CONTENT_IDENTITY_POLICY_FIELDS)}"
            )
            identity = {}
        identity_mode = identity.get("mode")
        if identity_mode not in CONTENT_IDENTITY_MODES:
            failures.append(f"{location}/content_identity_policy/mode: unsupported mode")
        if lifecycle == "active" and identity_mode not in {
            "platform-adapter-only",
            "canonical-pinned-snapshot-or-platform-adapter",
            "canonical-pinned-open-snapshot-or-platform-adapter",
        }:
            failures.append(
                f"{location}/content_identity_policy/mode: active authority requires an implemented resolution mode"
            )
        expected_identity_mode = "unresolved" if lifecycle == "planned" else identity_mode
        if lifecycle == "planned" and identity_mode != expected_identity_mode:
            failures.append(f"{location}/content_identity_policy/mode: planned authority must remain unresolved")
        expected_unpinned_action = "block" if lifecycle == "planned" else "adapter-required"
        if identity.get("unpinned_action") != expected_unpinned_action:
            failures.append(
                f"{location}/content_identity_policy/unpinned_action: expected "
                f"{expected_unpinned_action!r}"
            )
        pinned_mode = identity_mode in {
            "canonical-pinned-snapshot-or-platform-adapter",
            "canonical-pinned-open-snapshot-or-platform-adapter",
        }
        expected_resolution = (
            "unresolved"
            if lifecycle == "planned"
            else "canonical-pin-or-platform-verified"
            if pinned_mode
            else "platform-verified-only"
        )
        if content.get("resolution_mode") != expected_resolution:
            failures.append(f"{location}/content_policy/resolution_mode: expected {expected_resolution!r}")

        canonical = entry.get("canonical_snapshot")
        if lifecycle == "planned" or identity_mode == "platform-adapter-only":
            if canonical is not None:
                failures.append(f"{location}/canonical_snapshot: this content identity mode forbids a snapshot")
            canonical_projections[authority_id] = None
        elif pinned_mode:
            if lifecycle != "active":
                failures.append(f"{location}/content_identity_policy/mode: pinned mode requires an active authority")
            if canonical is None:
                failures.append(f"{location}/canonical_snapshot: pinned mode requires a canonical snapshot")
            canonical_failures, canonical_projection = _canonical_snapshot_projection(
                authority_id,
                entry,
                source_root,
                provider_skills.get(provider_id) if isinstance(provider_id, str) else None,
                externalized_receipts=externalized_receipts,
                used_externalized_paths=used_externalized_paths,
            )
            failures.extend(canonical_failures)
            canonical_projections[authority_id] = canonical_projection
        else:
            if canonical is not None:
                failures.append(f"{location}/canonical_snapshot: unsupported identity mode cannot authorize a snapshot")
            canonical_projections[authority_id] = None

        if lifecycle == "planned" and (
            origins or allowed_scopes or registered_scopes
        ):
            failures.append(f"{location}: planned authority must not claim verified source metadata")

    if software_data is not None:
        software = software_data.get("software")
        planned = software_data.get("planned_software")
        if not isinstance(software, dict) or not isinstance(planned, dict):
            failures.append("software-registry: expected software and planned_software mappings")
        else:
            active_providers = {
                provider_id
                for provider_id, specification in software.items()
                if isinstance(specification, dict) and specification.get("lifecycle") == "active"
            }
            planned_providers = set(planned)
            known_software_providers = active_providers | planned_providers
            active_authority_providers = set(
                software_providers_by_authority_lifecycle["active"]
            )
            planned_authority_providers = set(
                software_providers_by_authority_lifecycle["planned"]
            )
            unknown_authority_providers = (
                active_authority_providers
                | planned_authority_providers
            ) - known_software_providers
            if unknown_authority_providers:
                failures.append(
                    "authorities: software-class authority providers must exist "
                    "in active or planned software registry entries"
                )
            missing_active_authorities = (
                active_providers - active_authority_providers
            )
            if missing_active_authorities:
                failures.append(
                    "authorities: every active software provider requires at "
                    "least one active software-class authority"
                )
            missing_planned_authorities = planned_providers - (
                active_authority_providers | planned_authority_providers
            )
            if missing_planned_authorities:
                failures.append(
                    "authorities: every planned software provider requires at "
                    "least one active or planned software-class authority"
                )
    if failures:
        return failures, {}

    snapshot: dict[str, dict[str, Any]] = {}
    for authority_id, entry in authorities.items():
        if entry["lifecycle"] != "active":
            continue
        origins = entry["allowed_https_origins"]
        prefixes = entry["content_policy"]["allowed_path_prefixes"]
        snapshot[authority_id] = {
            "lifecycle": "active",
            "provider_class": entry["provider_class"],
            "provider_id": entry["provider_id"],
            "allowed_https_origins": copy.deepcopy(origins),
            "allowed_path_prefixes": copy.deepcopy(prefixes),
            "allowed_query_urls": copy.deepcopy(
                entry["content_policy"]["allowed_query_urls"]
            ),
            "locator_policy": {
                "allowed_origins": copy.deepcopy(origins),
                "allowed_path_prefixes": copy.deepcopy(prefixes),
            },
            "canonical_urls": [f"{origin}{prefix}" for origin in origins for prefix in prefixes],
            "source_kinds": copy.deepcopy(entry["content_policy"]["source_kinds"]),
            "version_scopes": copy.deepcopy(entry["version_policy"]["registered_scopes"]),
            "content_identity_policy": copy.deepcopy(entry["content_identity_policy"]),
            "canonical_snapshot": copy.deepcopy(canonical_projections.get(authority_id)),
        }
    return [], snapshot


def validate_and_project(
    data: object,
    *,
    software_data: dict[str, Any] | None = None,
    source_root: Path | None = None,
    externalized_receipts: Mapping[str, Mapping[str, object]] | None = None,
    used_externalized_paths: set[str] | None = None,
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    """Compatibility alias for the policy-free technical projection."""

    return validate_and_project_technical(
        data,
        software_data=software_data,
        source_root=source_root,
        externalized_receipts=externalized_receipts,
        used_externalized_paths=used_externalized_paths,
    )


def validation_errors(
    data: object,
    *,
    software_data: dict[str, Any] | None = None,
    source_root: Path | None = None,
    externalized_receipts: Mapping[str, Mapping[str, object]] | None = None,
    used_externalized_paths: set[str] | None = None,
) -> list[str]:
    failures, _ = validate_and_project(
        data,
        software_data=software_data,
        source_root=source_root,
        externalized_receipts=externalized_receipts,
        used_externalized_paths=used_externalized_paths,
    )
    return failures


def active_authority_snapshot(
    data: dict[str, Any],
    *,
    software_data: dict[str, Any] | None = None,
    source_root: Path | None = None,
    externalized_receipts: Mapping[str, Mapping[str, object]] | None = None,
    used_externalized_paths: set[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Compatibility alias for :func:`active_authority_technical_snapshot`."""

    return active_authority_technical_snapshot(
        data,
        software_data=software_data,
        source_root=source_root,
        externalized_receipts=externalized_receipts,
        used_externalized_paths=used_externalized_paths,
    )


def active_authority_technical_snapshot(
    data: dict[str, Any],
    *,
    software_data: dict[str, Any] | None = None,
    source_root: Path | None = None,
    externalized_receipts: Mapping[str, Mapping[str, object]] | None = None,
    used_externalized_paths: set[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Return active authority/version/locator/content-identity data only."""

    failures, snapshot = validate_and_project_technical(
        data,
        software_data=software_data,
        source_root=source_root,
        externalized_receipts=externalized_receipts,
        used_externalized_paths=used_externalized_paths,
    )
    if failures:
        raise ValueError("invalid official-source authority registry: " + "; ".join(failures))
    return snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--software-registry", type=Path)
    args = parser.parse_args()
    try:
        data = load_registry(args.registry)
        software = load_yaml_strict(
            args.software_registry or repo_root() / "registry" / "software-registry.yaml",
            "software-registry.yaml",
        )
        failures = validation_errors(
            data,
            software_data=software,
            source_root=repo_root(),
        )
    except (OSError, ValueError) as exc:
        failures = [f"<registry>: {exc}"]
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 2
    active = active_authority_snapshot(
        data,
        software_data=software,
        source_root=repo_root(),
    )
    planned = sum(1 for entry in data["authorities"].values() if entry["lifecycle"] == "planned")
    print(f"PASS: active official-source authorities={len(active)}; planned placeholders={planned}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
