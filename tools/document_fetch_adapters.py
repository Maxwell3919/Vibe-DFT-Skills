#!/usr/bin/env python3
"""Validate document-fetch adapters and derive documentation coverage."""

from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any
from urllib.parse import urlsplit

import yaml

from registry_yaml import load_yaml_strict


SCHEMA_VERSION = "1.0"
ADAPTER_ID = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*-v[1-9][0-9]*$")
PROFILE_ID = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
QUERY_KEY = re.compile(r"^[A-Za-z][A-Za-z0-9._-]*$")
SHA1 = re.compile(r"^[a-f0-9]{40}$")
REQUIREMENT = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)(?:\s*[^;#]*)?(?:;.*)?$")

ROOT_FIELDS = {
    "schema_version",
    "selection_policy",
    "adapters",
    "community_profiles",
    "implementation_package_docs",
}
SELECTION_FIELDS = {
    "ordered_routes",
    "browser_fallback_conditions",
    "canonical_body_policy",
    "body_storage_policy",
    "unregistered_source_action",
}
ADAPTER_FIELDS = {
    "lifecycle",
    "implementation_path",
    "package_identity",
    "input_interface",
    "output_interface",
    "source_classes",
    "side_effects",
    "security_controls",
    "limits",
}
PACKAGE_IDENTITY_FIELDS = {
    "distribution",
    "exact_version",
    "upstream_url",
    "release_tag",
    "release_commit",
}
SECURITY_FIELDS = {
    "robots_required",
    "public_network_only",
    "credentials_forbidden",
    "cookies_input_forbidden",
    "proxy_forbidden",
    "stealth_forbidden",
    "custom_javascript_forbidden",
    "llm_extraction_forbidden",
    "screenshots_forbidden",
    "deep_crawl_forbidden",
    "cache_reuse_forbidden",
}
LIMIT_FIELDS = {
    "max_pages",
    "max_depth",
    "max_page_timeout_ms",
    "max_artifact_bytes",
    "max_robots_bytes",
    "max_redirects",
}
COMMUNITY_FIELDS = {
    "display_name",
    "allowed_origins",
    "allowed_path_prefixes",
    "allowed_query_keys",
    "minimum_delay_seconds",
    "robots_unavailable_action",
    "native_route_first",
    "public_access_only",
    "evidence_class",
    "claim_ceiling",
    "retention_policy",
}
PACKAGE_DOC_FIELDS = {
    "requirement_name",
    "allowed_origins",
    "allowed_path_prefixes",
    "allowed_query_keys",
    "version_binding",
    "retrieval_policy",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def registry_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / "registry" / "document-fetch-adapters.yaml"


def load_registry(path: Path | None = None) -> dict[str, Any]:
    return load_yaml_strict(path or registry_path(), "document-fetch-adapters.yaml")


def normalize_distribution(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def requirement_distributions(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = REQUIREMENT.fullmatch(stripped)
        if match is None:
            raise ValueError(f"requirements-dev.txt:{line_number}: unsupported requirement syntax")
        name = match.group(1)
        normalized = normalize_distribution(name)
        if normalized in result:
            raise ValueError(f"requirements-dev.txt:{line_number}: duplicate distribution {normalized!r}")
        result[normalized] = name
    return result


def _canonical_origin(value: object, *, allow_http: bool) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError:
        return False
    if parts.scheme not in ({"http", "https"} if allow_http else {"https"}):
        return False
    if not parts.hostname or parts.username is not None or parts.password is not None:
        return False
    if port is not None or parts.path not in {"", "/"} or parts.query or parts.fragment:
        return False
    host = parts.hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        return False
    if re.fullmatch(r"\d+(?:\.\d+){3}", host) or ":" in host:
        return False
    return value == f"{parts.scheme}://{host}"


def _profile_errors(
    value: object,
    location: str,
    failures: list[str],
    *,
    fields: set[str],
    allow_http: bool,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        failures.append(f"{location}: expected a mapping")
        return {}
    if set(value) != fields:
        failures.append(
            f"{location}: expected fields {sorted(fields)}, found {sorted(map(str, value))}"
        )
    origins = value.get("allowed_origins")
    if not isinstance(origins, list) or not origins:
        failures.append(f"{location}/allowed_origins: expected a nonempty list")
    else:
        if len(origins) != len(set(map(str, origins))):
            failures.append(f"{location}/allowed_origins: duplicate values are forbidden")
        for index, origin in enumerate(origins):
            if not _canonical_origin(origin, allow_http=allow_http):
                failures.append(f"{location}/allowed_origins/{index}: expected a canonical public origin")
    prefixes = value.get("allowed_path_prefixes")
    if not isinstance(prefixes, list) or not prefixes:
        failures.append(f"{location}/allowed_path_prefixes: expected a nonempty list")
    else:
        for index, prefix in enumerate(prefixes):
            if (
                not isinstance(prefix, str)
                or not prefix.startswith("/")
                or "?" in prefix
                or "#" in prefix
                or ".." in PurePosixPath(prefix).parts
            ):
                failures.append(f"{location}/allowed_path_prefixes/{index}: invalid path prefix")
    query_keys = value.get("allowed_query_keys")
    if not isinstance(query_keys, list):
        failures.append(f"{location}/allowed_query_keys: expected a list")
    else:
        if query_keys != sorted(set(query_keys)):
            failures.append(f"{location}/allowed_query_keys: expected sorted unique keys")
        for index, key in enumerate(query_keys):
            if not isinstance(key, str) or QUERY_KEY.fullmatch(key) is None:
                failures.append(f"{location}/allowed_query_keys/{index}: invalid query key")
    return value


def validation_errors(data: object, root: Path | None = None) -> list[str]:
    selected_root = (root or repo_root()).resolve()
    failures: list[str] = []
    if not isinstance(data, dict):
        return ["<root>: registry must be a mapping"]
    if set(data) != ROOT_FIELDS:
        failures.append(
            f"<root>: expected fields {sorted(ROOT_FIELDS)}, found {sorted(map(str, data))}"
        )
    if data.get("schema_version") != SCHEMA_VERSION:
        failures.append(f"schema_version: expected {SCHEMA_VERSION!r}")

    selection = data.get("selection_policy")
    if not isinstance(selection, dict) or set(selection) != SELECTION_FIELDS:
        failures.append(f"selection_policy: expected fields {sorted(SELECTION_FIELDS)}")
        selection = {}
    if selection.get("ordered_routes") != [
        "registered-pinned-receipt",
        "registered-provider-api",
        "registered-direct-http",
        "crawl4ai-render-v1",
    ]:
        failures.append("selection_policy/ordered_routes: native routes must precede Crawl4AI")
    if selection.get("browser_fallback_conditions") != [
        "javascript-required",
        "browser-render-required",
        "native-response-incomplete",
    ]:
        failures.append("selection_policy/browser_fallback_conditions: unsupported fallback policy")
    if selection.get("canonical_body_policy") != "browser-rendered-bodies-are-derived-only":
        failures.append("selection_policy/canonical_body_policy: browser output must remain derived")
    if selection.get("body_storage_policy") != "outside-git-content-addressed":
        failures.append("selection_policy/body_storage_policy: bodies must remain outside Git")
    if selection.get("unregistered_source_action") != "block":
        failures.append("selection_policy/unregistered_source_action: expected block")

    adapters = data.get("adapters")
    if not isinstance(adapters, dict) or set(adapters) != {"crawl4ai-render-v1"}:
        failures.append("adapters: expected exactly crawl4ai-render-v1")
        adapters = {}
    adapter = adapters.get("crawl4ai-render-v1")
    if not isinstance(adapter, dict) or set(adapter) != ADAPTER_FIELDS:
        failures.append(f"adapters/crawl4ai-render-v1: expected fields {sorted(ADAPTER_FIELDS)}")
        adapter = {}
    if adapter.get("lifecycle") != "active":
        failures.append("adapters/crawl4ai-render-v1/lifecycle: expected active")
    implementation = adapter.get("implementation_path")
    if implementation != "tools/crawl4ai_capture.py":
        failures.append("adapters/crawl4ai-render-v1/implementation_path: unexpected adapter path")
    elif not selected_root.joinpath(implementation).is_file():
        failures.append("adapters/crawl4ai-render-v1/implementation_path: adapter is missing")
    package = adapter.get("package_identity")
    if not isinstance(package, dict) or set(package) != PACKAGE_IDENTITY_FIELDS:
        failures.append("adapters/crawl4ai-render-v1/package_identity: invalid package identity")
        package = {}
    if package.get("distribution") != "Crawl4AI" or package.get("exact_version") != "0.9.2":
        failures.append("adapters/crawl4ai-render-v1/package_identity: exact Crawl4AI 0.9.2 is required")
    if package.get("upstream_url") != "https://github.com/unclecode/crawl4ai":
        failures.append("adapters/crawl4ai-render-v1/package_identity/upstream_url: unexpected upstream")
    if package.get("release_tag") != "v0.9.2" or not isinstance(package.get("release_commit"), str) or SHA1.fullmatch(package["release_commit"]) is None:
        failures.append("adapters/crawl4ai-render-v1/package_identity: invalid release identity")
    if adapter.get("input_interface") != "web-source-capture-request@1.0":
        failures.append("adapters/crawl4ai-render-v1/input_interface: unexpected interface")
    if adapter.get("output_interface") != "web-source-capture-manifest@1.0":
        failures.append("adapters/crawl4ai-render-v1/output_interface: unexpected interface")
    if adapter.get("source_classes") != ["official-software", "official-package", "public-community"]:
        failures.append("adapters/crawl4ai-render-v1/source_classes: unsupported source classes")
    if adapter.get("side_effects") != ["network-read", "local-write", "local-browser-execution"]:
        failures.append("adapters/crawl4ai-render-v1/side_effects: unsupported side-effect boundary")
    controls = adapter.get("security_controls")
    if not isinstance(controls, dict) or set(controls) != SECURITY_FIELDS:
        failures.append("adapters/crawl4ai-render-v1/security_controls: invalid controls")
    elif any(controls.get(field) is not True for field in SECURITY_FIELDS):
        failures.append("adapters/crawl4ai-render-v1/security_controls: every fail-closed control must be true")
    limits = adapter.get("limits")
    if not isinstance(limits, dict) or set(limits) != LIMIT_FIELDS:
        failures.append("adapters/crawl4ai-render-v1/limits: invalid limits")
    elif limits != {
        "max_pages": 1,
        "max_depth": 0,
        "max_page_timeout_ms": 60000,
        "max_artifact_bytes": 16777216,
        "max_robots_bytes": 524288,
        "max_redirects": 5,
    }:
        failures.append("adapters/crawl4ai-render-v1/limits: limits exceed the reviewed single-page profile")

    communities = data.get("community_profiles")
    if not isinstance(communities, dict) or not communities:
        failures.append("community_profiles: expected a nonempty mapping")
        communities = {}
    for profile_id, value in communities.items():
        location = f"community_profiles/{profile_id}"
        if not isinstance(profile_id, str) or PROFILE_ID.fullmatch(profile_id) is None:
            failures.append(f"{location}: invalid profile identifier")
        profile = _profile_errors(value, location, failures, fields=COMMUNITY_FIELDS, allow_http=True)
        if not isinstance(profile.get("display_name"), str) or not profile.get("display_name", "").strip():
            failures.append(f"{location}/display_name: expected a nonempty string")
        delay = profile.get("minimum_delay_seconds")
        if not isinstance(delay, int) or isinstance(delay, bool) or not 1 <= delay <= 60:
            failures.append(f"{location}/minimum_delay_seconds: expected 1..60")
        fixed = {
            "robots_unavailable_action": "block",
            "native_route_first": True,
            "public_access_only": True,
            "evidence_class": "community-source-claim",
            "claim_ceiling": "source-claim-only",
            "retention_policy": "manifest-and-private-body-outside-git",
        }
        for field, expected in fixed.items():
            if profile.get(field) != expected:
                failures.append(f"{location}/{field}: expected {expected!r}")

    package_docs = data.get("implementation_package_docs")
    if not isinstance(package_docs, dict) or not package_docs:
        failures.append("implementation_package_docs: expected a nonempty mapping")
        package_docs = {}
    try:
        required = requirement_distributions(selected_root / "requirements-dev.txt")
    except (OSError, UnicodeError, ValueError) as exc:
        failures.append(f"requirements-dev.txt: cannot derive package coverage ({exc})")
        required = {}
    if set(package_docs) != set(required):
        failures.append(
            "implementation_package_docs: keys must exactly cover normalized requirements-dev.txt distributions"
        )
    for package_id, value in package_docs.items():
        location = f"implementation_package_docs/{package_id}"
        if normalize_distribution(str(package_id)) != package_id:
            failures.append(f"{location}: expected a normalized distribution identifier")
        profile = _profile_errors(value, location, failures, fields=PACKAGE_DOC_FIELDS, allow_http=False)
        if required.get(package_id) != profile.get("requirement_name"):
            failures.append(f"{location}/requirement_name: must match requirements-dev.txt spelling")
        if profile.get("version_binding") not in {
            "installed-version-required-before-version-sensitive-use",
            "exact-tag-or-commit-required-before-version-sensitive-use",
        }:
            failures.append(f"{location}/version_binding: unsupported policy")
        if profile.get("retrieval_policy") not in {
            "native-first-browser-fallback",
            "native-git-first-browser-fallback",
        }:
            failures.append(f"{location}/retrieval_policy: unsupported policy")
    return failures


def coverage_summary(data: dict[str, Any], root: Path | None = None) -> dict[str, int]:
    selected_root = (root or repo_root()).resolve()
    failures = validation_errors(data, selected_root)
    if failures:
        raise ValueError("invalid document-fetch adapter registry: " + "; ".join(failures))
    software = load_yaml_strict(
        selected_root / "registry" / "software-registry.yaml",
        "software-registry.yaml",
    )
    authorities = load_yaml_strict(
        selected_root / "registry" / "official-source-authorities.yaml",
        "official-source-authorities.yaml",
    )
    active_software = {
        provider_id
        for provider_id, specification in software["software"].items()
        if specification["lifecycle"] == "active"
    }
    planned_software = set(software["planned_software"])
    active_authority_providers = {
        item["provider_id"]
        for item in authorities["authorities"].values()
        if item["provider_class"] == "software" and item["lifecycle"] == "active"
    }
    planned_authority_providers = {
        item["provider_id"]
        for item in authorities["authorities"].values()
        if item["provider_class"] == "software" and item["lifecycle"] == "planned"
    }
    if not active_software.issubset(active_authority_providers):
        raise ValueError("active scientific software lacks an active official-source route")
    if not planned_software.issubset(active_authority_providers | planned_authority_providers):
        raise ValueError("planned scientific software lacks official-source metadata")
    return {
        "adapters": len(data["adapters"]),
        "community_profiles": len(data["community_profiles"]),
        "implementation_packages": len(data["implementation_package_docs"]),
        "scientific_software": len(active_software) + len(planned_software),
        "active_scientific_software": len(active_software),
        "planned_scientific_software": len(planned_software),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    root = (args.root or repo_root()).resolve()
    try:
        data = load_registry(args.registry or registry_path(root))
        failures = validation_errors(data, root)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
        failures = [f"<registry>: {exc}"]
        data = {}
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 2
    summary = coverage_summary(data, root)
    print(
        "PASS: document-fetch registry binds "
        f"{summary['adapters']} controlled adapter, "
        f"{summary['community_profiles']} public community profiles, and "
        f"{summary['implementation_packages']} requirement-derived package documentation profiles; "
        f"official-source coverage is registered for {summary['scientific_software']} scientific "
        f"software identities ({summary['active_scientific_software']} active routes, "
        f"{summary['planned_scientific_software']} planned metadata-only routes)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
