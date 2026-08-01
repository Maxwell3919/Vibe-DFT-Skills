#!/usr/bin/env python3
"""Plan, run, and validate one fail-closed Crawl4AI source capture."""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import importlib.metadata
import ipaddress
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import socket
import sys
import tempfile
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    ProxyHandler,
    Request,
    build_opener,
)
from urllib.robotparser import RobotFileParser

from jsonschema import Draft202012Validator, FormatChecker
from bs4 import BeautifulSoup

import document_fetch_adapters
from official_source_authorities import validate_and_project_technical
from registry_yaml import load_yaml_strict
from software_registry import load_registry as load_software_registry
from strict_json import StrictJSONError, load_object, read_bytes_bounded


USER_AGENT = "Vibe-DFT-Skills-document-capture/1.0"
REQUEST_INTERFACE = "web-source-capture-request@1.0"
MANIFEST_INTERFACE = "web-source-capture-manifest@1.0"
REQUEST_SCHEMA = "web-source-capture-request.schema.json"
MANIFEST_SCHEMA = "web-source-capture-manifest.schema.json"
ADAPTER_ID = "crawl4ai-render-v1"
CONTROL_RECEIPT = [
    "robots-required",
    "public-network-only",
    "credentials-forbidden",
    "cookie-input-forbidden",
    "proxy-forbidden",
    "stealth-forbidden",
    "custom-javascript-forbidden",
    "llm-extraction-forbidden",
    "screenshots-forbidden",
    "deep-crawl-forbidden",
    "cache-reuse-forbidden",
]
ROLE_PATHS = {
    "capture-request": "request.json",
    "robots-policy": "robots.txt",
    "direct-response": "direct-response.bin",
    "rendered-dom": "rendered.html",
    "readable-markdown": "content.md",
}
ROLE_IDENTITIES = {
    "capture-request": "request-evidence",
    "robots-policy": "transport-evidence",
    "direct-response": "transport-evidence",
    "rendered-dom": "rendered-derivative",
    "readable-markdown": "readable-derivative",
}


class CaptureBlocked(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class CaptureFailed(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def is_within(candidate: Path, parent: Path) -> bool:
    candidate_resolved = candidate.resolve(strict=False)
    parent_resolved = parent.resolve(strict=False)
    return candidate_resolved == parent_resolved or parent_resolved in candidate_resolved.parents


def expected_robots_url(value: str) -> str:
    parts, _origin = parsed_http_url(value, allow_http=True)
    return f"{parts.scheme}://{parts.hostname.lower().rstrip('.')}/robots.txt"


def deterministic_request_id(request: dict[str, Any]) -> str:
    identity = {
        "source_class": request["source_class"],
        "profile_id": request["profile_id"],
        "url": request["url"],
        "fallback_condition": request["native_route"]["fallback_condition"],
        "native_evidence": request["native_route"]["evidence"],
        "required_css_selectors": request["content_gate"]["required_css_selectors"],
        "required_markdown_substrings": request["content_gate"]["required_markdown_substrings"],
        "forbidden_markdown_substrings": request["content_gate"]["forbidden_markdown_substrings"],
        "minimum_markdown_bytes": request["content_gate"]["minimum_markdown_bytes"],
        "page_timeout_ms": request["limits"]["page_timeout_ms"],
    }
    return f"capture-request-{sha256(canonical_json(identity))[:24]}"


def deterministic_record_id(request_raw: bytes, captured_utc: str) -> str:
    return f"web-capture-{sha256(request_raw + captured_utc.encode('ascii'))[:24]}"


def load_schema(root: Path, name: str) -> dict[str, Any]:
    return load_object(root / "contracts" / name, name, max_bytes=2 * 1024 * 1024)


def schema_errors(value: object, schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(value), key=lambda item: list(item.absolute_path))
    ]


@lru_cache(maxsize=4)
def load_registries(root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    adapter_data = document_fetch_adapters.load_registry(
        root / "registry" / "document-fetch-adapters.yaml"
    )
    adapter_failures = document_fetch_adapters.validation_errors(adapter_data, root)
    if adapter_failures:
        raise CaptureBlocked("ADAPTER_REGISTRY_INVALID")
    software_data = load_software_registry(root / "registry" / "software-registry.yaml")
    authority_data = load_yaml_strict(
        root / "registry" / "official-source-authorities.yaml",
        "official-source-authorities.yaml",
    )
    failures, projection = validate_and_project_technical(
        authority_data,
        software_data=software_data,
        source_root=root,
    )
    if failures:
        raise CaptureBlocked("OFFICIAL_AUTHORITY_REGISTRY_INVALID")
    return adapter_data, projection


def source_profile(
    request: dict[str, Any],
    adapter_data: dict[str, Any],
    authorities: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_class = request["source_class"]
    profile_id = request["profile_id"]
    if source_class == "official-software":
        entry = authorities.get(profile_id)
        if entry is None:
            raise CaptureBlocked("UNREGISTERED_OR_INACTIVE_OFFICIAL_AUTHORITY")
        return {
            "allowed_origins": entry["allowed_https_origins"],
            "allowed_path_prefixes": entry["allowed_path_prefixes"],
            "allowed_query_keys": [],
            "allowed_query_urls": entry["allowed_query_urls"],
            "minimum_delay_seconds": 1,
            "allow_http": False,
        }
    if source_class == "official-package":
        entry = adapter_data["implementation_package_docs"].get(profile_id)
        if entry is None:
            raise CaptureBlocked("UNREGISTERED_PACKAGE_PROFILE")
        return {
            **entry,
            "allowed_query_urls": [],
            "minimum_delay_seconds": 1,
            "allow_http": False,
        }
    entry = adapter_data["community_profiles"].get(profile_id)
    if entry is None:
        raise CaptureBlocked("UNREGISTERED_COMMUNITY_PROFILE")
    return {
        **entry,
        "allowed_query_urls": [],
        "allow_http": True,
    }


def parsed_http_url(value: str, *, allow_http: bool) -> tuple[Any, str]:
    try:
        parts = urlsplit(value)
        port = parts.port
    except (TypeError, ValueError) as exc:
        raise CaptureBlocked("URL_INVALID") from exc
    schemes = {"http", "https"} if allow_http else {"https"}
    if parts.scheme not in schemes or not parts.hostname:
        raise CaptureBlocked("URL_SCHEME_OR_HOST_BLOCKED")
    if parts.username is not None or parts.password is not None or parts.fragment:
        raise CaptureBlocked("URL_CREDENTIAL_OR_FRAGMENT_BLOCKED")
    if port is not None:
        raise CaptureBlocked("URL_EXPLICIT_PORT_BLOCKED")
    host = parts.hostname.lower().rstrip(".")
    origin = f"{parts.scheme}://{host}"
    return parts, origin


def validate_profile_url(value: str, profile: dict[str, Any]) -> None:
    parts, origin = parsed_http_url(value, allow_http=bool(profile["allow_http"]))
    if origin not in profile["allowed_origins"]:
        raise CaptureBlocked("URL_ORIGIN_OUTSIDE_PROFILE")
    path = parts.path or "/"
    if ".." in PurePosixPath(path).parts or not any(
        path.startswith(prefix) for prefix in profile["allowed_path_prefixes"]
    ):
        raise CaptureBlocked("URL_PATH_OUTSIDE_PROFILE")
    pairs = parse_qsl(parts.query, keep_blank_values=True, strict_parsing=False)
    keys = [key for key, _value in pairs]
    if len(keys) != len(set(keys)):
        raise CaptureBlocked("URL_DUPLICATE_QUERY_KEY")
    exact_urls = profile.get("allowed_query_urls", [])
    if parts.query and exact_urls:
        if value not in exact_urls:
            raise CaptureBlocked("URL_QUERY_OUTSIDE_EXACT_ALLOWLIST")
    elif any(key not in profile.get("allowed_query_keys", []) for key in keys):
        raise CaptureBlocked("URL_QUERY_KEY_OUTSIDE_PROFILE")


def assert_public_destination(value: str) -> None:
    parts, _origin = parsed_http_url(value, allow_http=True)
    host = parts.hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise CaptureBlocked("PRIVATE_NETWORK_DESTINATION")
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        if not literal.is_global:
            raise CaptureBlocked("PRIVATE_NETWORK_DESTINATION")
        return
    try:
        addresses = {
            ipaddress.ip_address(item[4][0])
            for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        }
    except (OSError, ValueError) as exc:
        raise CaptureBlocked("DNS_RESOLUTION_FAILED") from exc
    if not addresses or any(not address.is_global for address in addresses):
        raise CaptureBlocked("PRIVATE_NETWORK_DESTINATION")


class SafeRedirectHandler(HTTPRedirectHandler):
    def __init__(self, profile: dict[str, Any], max_redirects: int):
        super().__init__()
        self.profile = profile
        self.max_redirects = max_redirects
        self.redirects = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        self.redirects += 1
        if self.redirects > self.max_redirects:
            raise CaptureBlocked("REDIRECT_LIMIT_EXCEEDED")
        validate_profile_url(newurl, self.profile)
        assert_public_destination(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_bytes(
    url: str,
    profile: dict[str, Any],
    *,
    max_bytes: int,
    max_redirects: int,
) -> tuple[bytes, int, str, str]:
    validate_profile_url(url, profile)
    assert_public_destination(url)
    opener = build_opener(ProxyHandler({}), SafeRedirectHandler(profile, max_redirects))
    request = Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
        method="GET",
    )
    with opener.open(request, timeout=45) as response:
        length = response.headers.get("Content-Length")
        if length is not None and int(length) > max_bytes:
            raise CaptureBlocked("RESPONSE_TOO_LARGE")
        raw = response.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raise CaptureBlocked("RESPONSE_TOO_LARGE")
        final_url = response.geturl()
        validate_profile_url(final_url, profile)
        assert_public_destination(final_url)
        media_type = response.headers.get_content_type() or "application/octet-stream"
        return raw, int(response.status), final_url, media_type


def robots_receipt(
    url: str,
    profile: dict[str, Any],
    *,
    max_bytes: int,
    max_redirects: int,
) -> tuple[str, str, bytes | None, int]:
    parsed_http_url(url, allow_http=bool(profile["allow_http"]))
    robots_url = expected_robots_url(url)
    try:
        raw, status, _final_url, _media_type = fetch_bytes(
            robots_url,
            {
                **profile,
                "allowed_path_prefixes": ["/robots.txt"],
                "allowed_query_keys": [],
                "allowed_query_urls": [],
            },
            max_bytes=max_bytes,
            max_redirects=max_redirects,
        )
    except (HTTPError, URLError, TimeoutError, OSError, CaptureBlocked):
        return robots_url, "unavailable", None, int(profile["minimum_delay_seconds"])
    if status != 200:
        return robots_url, "unavailable", raw, int(profile["minimum_delay_seconds"])
    parser = RobotFileParser()
    parser.set_url(robots_url)
    parser.parse(raw.decode("utf-8", errors="replace").splitlines())
    allowed = parser.can_fetch(USER_AGENT, url)
    delay = parser.crawl_delay(USER_AGENT) or parser.crawl_delay("*") or 0
    if not isinstance(delay, (int, float)) or delay < 0 or delay > 60:
        return robots_url, "unavailable", raw, int(profile["minimum_delay_seconds"])
    minimum = max(int(profile["minimum_delay_seconds"]), int(delay))
    return robots_url, "allowed" if allowed else "blocked", raw, minimum


def artifact(path: Path, role: str, media_type: str, identity_role: str) -> dict[str, Any]:
    raw = path.read_bytes()
    return {
        "role": role,
        "path": path.name,
        "sha256": sha256(raw),
        "bytes": len(raw),
        "media_type": media_type,
        "identity_role": identity_role,
    }


def write_artifact(stage: Path, name: str, raw: bytes, max_bytes: int) -> Path:
    if len(raw) > max_bytes:
        raise CaptureBlocked("ARTIFACT_TOO_LARGE")
    path = stage / name
    path.write_bytes(raw)
    return path


def claim_ceiling(source_class: str) -> dict[str, Any]:
    return {
        "document_identity": "derived-browser-render-only",
        "community_evidence": "source-claim-only" if source_class == "public-community" else "not-applicable",
        "scientific": "no-scientific-claim",
        "version_sensitive_use": False,
    }


def adapter_config(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "browser_type": "chromium",
        "headless": True,
        "user_agent": USER_AGENT,
        "cache_mode": "BYPASS",
        "check_robots_txt": True,
        "page_timeout_ms": request["limits"]["page_timeout_ms"],
        "wait_until": "domcontentloaded",
        "proxy": None,
        "simulate_user": False,
        "override_navigator": False,
        "magic": False,
        "custom_javascript": None,
        "llm_extraction": None,
        "screenshot": False,
        "deep_crawl": False,
    }


def content_gate_passes(request: dict[str, Any], rendered: str, markdown: str) -> bool:
    gate = request["content_gate"]
    if len(markdown.encode("utf-8")) < gate["minimum_markdown_bytes"]:
        return False
    document = BeautifulSoup(rendered, "html.parser")
    if any(not document.select(selector) for selector in gate["required_css_selectors"]):
        return False
    if any(value not in markdown for value in gate["required_markdown_substrings"]):
        return False
    if any(value in markdown for value in gate["forbidden_markdown_substrings"]):
        return False
    return True


def runtime_version() -> str:
    try:
        version = importlib.metadata.version("Crawl4AI")
    except importlib.metadata.PackageNotFoundError as exc:
        raise CaptureBlocked("CRAWL4AI_RUNTIME_MISSING") from exc
    if version != "0.9.2":
        raise CaptureBlocked("CRAWL4AI_VERSION_MISMATCH")
    return version


async def browser_capture(
    request: dict[str, Any],
    profile: dict[str, Any],
) -> tuple[str, str, str, int | None, int, str, str]:
    runtime_version()
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
    except (ImportError, RuntimeError) as exc:
        raise CaptureBlocked("CRAWL4AI_IMPORT_FAILED") from exc

    blocked_requests = 0
    playwright_version = importlib.metadata.version("playwright")
    browser_version = "unknown"
    browser = BrowserConfig(
        browser_type="chromium",
        headless=True,
        user_agent=USER_AGENT,
        user_agent_mode="",
        proxy_config=None,
        use_managed_browser=False,
        verbose=False,
    )
    run = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        check_robots_txt=True,
        page_timeout=request["limits"]["page_timeout_ms"],
        wait_until="domcontentloaded",
        simulate_user=False,
        override_navigator=False,
        magic=False,
        screenshot=False,
        pdf=False,
        capture_mhtml=False,
        js_code=None,
        wait_for=None,
    )
    try:
        async with AsyncWebCrawler(config=browser) as crawler:
            browser_version = crawler.crawler_strategy.browser_manager.browser.version
            async def install_network_guard(page, **_kwargs):  # noqa: ANN001
                async def guard(route, playwright_request):  # noqa: ANN001
                    nonlocal blocked_requests
                    destination = playwright_request.url
                    scheme = urlsplit(destination).scheme
                    try:
                        if scheme in {"data", "blob", "about"}:
                            await route.continue_()
                            return
                        await asyncio.to_thread(assert_public_destination, destination)
                        if playwright_request.is_navigation_request() and playwright_request.frame == page.main_frame:
                            validate_profile_url(destination, profile)
                        await route.continue_()
                    except (CaptureBlocked, OSError, ValueError):
                        blocked_requests += 1
                        await route.abort("blockedbyclient")
                await page.route("**/*", guard)
                return page

            crawler.crawler_strategy.set_hook("on_page_context_created", install_network_guard)
            result = await crawler.arun(url=request["url"], config=run)
    except CaptureBlocked:
        raise
    except Exception as exc:  # Crawl4AI and Playwright expose several runtime-specific errors.
        raise CaptureFailed("BROWSER_EXECUTION_FAILED") from exc
    if not result.success:
        if result.response_headers and result.response_headers.get("X-Robots-Status"):
            raise CaptureBlocked("ROBOTS_BLOCKED_BY_RUNTIME")
        raise CaptureFailed("CRAWL4AI_RESULT_FAILED")
    final_url = result.redirected_url or result.url
    validate_profile_url(final_url, profile)
    assert_public_destination(final_url)
    rendered = result.html or ""
    markdown_value = result.markdown
    markdown = getattr(markdown_value, "raw_markdown", None) or str(markdown_value or "")
    if not rendered.strip() or not markdown.strip():
        raise CaptureFailed("EMPTY_RENDERED_RESULT")
    return (
        rendered,
        markdown,
        final_url,
        result.status_code,
        blocked_requests,
        playwright_version,
        browser_version,
    )


def base_manifest(
    request: dict[str, Any],
    request_raw: bytes,
    captured_utc: str,
    config_sha: str,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "contract_name": "web-source-capture-manifest",
        "record_id": deterministic_record_id(request_raw, captured_utc),
        "captured_utc": captured_utc,
        "request_ref": {"request_id": request["request_id"], "sha256": sha256(request_raw)},
        "status": "failed",
        "source": {
            "source_class": request["source_class"],
            "profile_id": request["profile_id"],
            "requested_url": request["url"],
            "final_url": None,
        },
        "adapter": {
            "adapter_id": ADAPTER_ID,
            "distribution": "Crawl4AI",
            "distribution_version": "0.9.2",
            "upstream_release": "v0.9.2",
            "upstream_commit": "7e801521428ee12509994d39151006f64055ebe3",
            "browser_type": "chromium",
            "playwright_version": None,
            "browser_version": None,
            "config_sha256": config_sha,
        },
        "policy": {
            "robots_url": expected_robots_url(request["url"]),
            "robots_status": "unavailable",
            "robots_sha256": None,
            "robots_bytes": None,
            "minimum_delay_seconds": 1,
            "final_url_profile_verified": False,
            "blocked_network_requests": 0,
            "controls_enforced": CONTROL_RECEIPT,
        },
        "artifacts": [],
        "result": {
            "http_status": None,
            "error_code": "CAPTURE_NOT_STARTED",
            "content_gate_passed": False,
        },
        "claim_ceiling": claim_ceiling(request["source_class"]),
    }


def ensure_output_scope(output: Path, root: Path) -> None:
    resolved = output.resolve(strict=False)
    if is_within(resolved, root):
        raise CaptureBlocked("OUTPUT_INSIDE_GIT_WORKTREE")
    if output.exists() or output.is_symlink():
        raise CaptureBlocked("OUTPUT_ALREADY_EXISTS")
    resolved.parent.mkdir(parents=True, exist_ok=True)


def run_capture(request_path: Path, output: Path, root: Path) -> tuple[int, dict[str, Any]]:
    request_raw = read_bytes_bounded(request_path, request_path.name, max_bytes=256 * 1024)
    request = load_object(request_path, request_path.name, max_bytes=256 * 1024)
    request_failures = schema_errors(request, load_schema(root, REQUEST_SCHEMA))
    if request_failures:
        raise CaptureBlocked("REQUEST_SCHEMA_INVALID")
    adapter_data, authorities = load_registries(root)
    profile = source_profile(request, adapter_data, authorities)
    validate_profile_url(request["url"], profile)
    ensure_output_scope(output, root)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.resolve(strict=False).parent))
    captured_utc = utc_now()
    config_sha = sha256(canonical_json(adapter_config(request)))
    manifest = base_manifest(request, request_raw, captured_utc, config_sha)
    max_bytes = request["limits"]["max_artifact_bytes"]
    limits = adapter_data["adapters"][ADAPTER_ID]["limits"]
    try:
        request_copy = write_artifact(stage, "request.json", request_raw, max_bytes)
        manifest["artifacts"].append(
            artifact(request_copy, "capture-request", "application/json", "request-evidence")
        )
        robots_url, robots_status, robots_raw, delay = robots_receipt(
            request["url"],
            profile,
            max_bytes=limits["max_robots_bytes"],
            max_redirects=limits["max_redirects"],
        )
        manifest["policy"].update(
            {
                "robots_url": robots_url,
                "robots_status": robots_status,
                "robots_sha256": sha256(robots_raw) if robots_raw is not None else None,
                "robots_bytes": len(robots_raw) if robots_raw is not None else None,
                "minimum_delay_seconds": delay,
            }
        )
        if robots_raw is not None:
            robots_path = write_artifact(stage, "robots.txt", robots_raw, max_bytes)
            manifest["artifacts"].append(
                artifact(robots_path, "robots-policy", "text/plain", "transport-evidence")
            )
        if robots_status != "allowed":
            raise CaptureBlocked("ROBOTS_DISALLOWED" if robots_status == "blocked" else "ROBOTS_UNAVAILABLE")

        time.sleep(delay)
        try:
            direct_raw, _direct_status, _direct_url, direct_media = fetch_bytes(
                request["url"],
                profile,
                max_bytes=max_bytes,
                max_redirects=limits["max_redirects"],
            )
        except (HTTPError, URLError, TimeoutError, OSError):
            direct_raw = None
        if direct_raw is not None:
            direct_path = write_artifact(stage, "direct-response.bin", direct_raw, max_bytes)
            manifest["artifacts"].append(
                artifact(direct_path, "direct-response", direct_media, "transport-evidence")
            )

        time.sleep(delay)
        (
            rendered,
            markdown,
            final_url,
            http_status,
            blocked_requests,
            playwright_version,
            browser_version,
        ) = asyncio.run(
            browser_capture(request, profile)
        )
        rendered_path = write_artifact(stage, "rendered.html", rendered.encode("utf-8"), max_bytes)
        markdown_path = write_artifact(stage, "content.md", markdown.encode("utf-8"), max_bytes)
        manifest["artifacts"].extend(
            [
                artifact(rendered_path, "rendered-dom", "text/html; charset=utf-8", "rendered-derivative"),
                artifact(markdown_path, "readable-markdown", "text/markdown; charset=utf-8", "readable-derivative"),
            ]
        )
        manifest["source"]["final_url"] = final_url
        manifest["policy"]["final_url_profile_verified"] = True
        manifest["policy"]["blocked_network_requests"] = blocked_requests
        manifest["adapter"]["playwright_version"] = playwright_version
        manifest["adapter"]["browser_version"] = browser_version
        manifest["result"]["http_status"] = http_status
        if not isinstance(http_status, int) or not 200 <= http_status <= 299:
            raise CaptureFailed("HTTP_STATUS_NOT_SUCCESS")
        if not content_gate_passes(request, rendered, markdown):
            raise CaptureFailed("CONTENT_GATE_FAILED")
        manifest["status"] = "success"
        manifest["result"] = {
            "http_status": http_status,
            "error_code": None,
            "content_gate_passed": True,
        }
        exit_code = 0
    except CaptureBlocked as exc:
        manifest["status"] = "blocked"
        manifest["result"]["error_code"] = exc.code
        exit_code = 3
    except CaptureFailed as exc:
        manifest["status"] = "failed"
        manifest["result"]["error_code"] = exc.code
        exit_code = 4
    except Exception:
        manifest["status"] = "failed"
        manifest["result"]["error_code"] = "UNEXPECTED_CAPTURE_FAILURE"
        exit_code = 4

    manifest_failures = schema_errors(manifest, load_schema(root, MANIFEST_SCHEMA))
    if manifest_failures:
        shutil.rmtree(stage)
        raise CaptureFailed("MANIFEST_SCHEMA_INVALID")
    (stage / "manifest.json").write_bytes(canonical_json(manifest))
    os.replace(stage, output)
    return exit_code, manifest


def validate_capture(manifest_path: Path, artifact_root: Path, root: Path) -> list[str]:
    failures: list[str] = []
    try:
        root_resolved = artifact_root.resolve(strict=True)
        if not artifact_root.is_dir() or artifact_root.is_symlink():
            raise OSError("unsafe artifact root")
    except OSError:
        return ["artifact_root: missing or unsafe directory"]
    if is_within(root_resolved, root):
        failures.append("artifact_root: capture directory is inside the Git worktree")
    try:
        manifest_resolved = manifest_path.resolve(strict=True)
        if (
            manifest_resolved != root_resolved / "manifest.json"
            or manifest_path.is_symlink()
            or not manifest_path.is_file()
        ):
            raise OSError("unsafe manifest")
    except OSError:
        return failures + ["manifest: must be the regular artifact-root/manifest.json file"]
    try:
        manifest = load_object(manifest_path, manifest_path.name, max_bytes=2 * 1024 * 1024)
    except (OSError, StrictJSONError) as exc:
        return [f"manifest: {exc}"]
    failures.extend(schema_errors(manifest, load_schema(root, MANIFEST_SCHEMA)))
    roles: set[str] = set()
    role_paths: dict[str, Path] = {}
    role_bytes: dict[str, bytes] = {}
    bound_request: dict[str, Any] | None = None
    bound_profile: dict[str, Any] | None = None
    for index, item in enumerate(manifest.get("artifacts", [])):
        role = item.get("role") if isinstance(item, dict) else None
        if role in roles:
            failures.append(f"artifacts/{index}/role: duplicate role")
        if isinstance(role, str):
            roles.add(role)
        relative = item.get("path") if isinstance(item, dict) else None
        if not isinstance(relative, str):
            continue
        if isinstance(role, str) and relative != ROLE_PATHS.get(role):
            failures.append(f"artifacts/{index}/path: role must use its canonical path")
        if isinstance(role, str) and item.get("identity_role") != ROLE_IDENTITIES.get(role):
            failures.append(f"artifacts/{index}/identity_role: role identity mismatch")
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts:
            failures.append(f"artifacts/{index}/path: unsafe path")
            continue
        path = artifact_root.joinpath(*pure.parts)
        try:
            resolved = path.resolve(strict=True)
            if root_resolved not in resolved.parents or path.is_symlink() or not path.is_file():
                raise OSError("unsafe")
            raw = read_bytes_bounded(path, relative, max_bytes=16777216)
        except (OSError, StrictJSONError):
            failures.append(f"artifacts/{index}/path: missing or unsafe artifact")
            continue
        if sha256(raw) != item.get("sha256") or len(raw) != item.get("bytes"):
            failures.append(f"artifacts/{index}: content identity mismatch")
        elif isinstance(role, str):
            role_paths[role] = path
            role_bytes[role] = raw
    expected_entries = {"manifest.json"} | {
        item.get("path")
        for item in manifest.get("artifacts", [])
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    observed_entries = {item.name for item in artifact_root.iterdir()}
    if observed_entries != expected_entries or any(
        item.is_symlink() or not item.is_file() for item in artifact_root.iterdir()
    ):
        failures.append("artifact_root: unmanifested, nested, or unsafe entries present")
    if "capture-request" in roles:
        try:
            request_path = role_paths["capture-request"]
            request_raw = read_bytes_bounded(request_path, "request.json", max_bytes=256 * 1024)
            request = load_object(request_path, "request.json", max_bytes=256 * 1024)
            bound_request = request
            failures.extend(f"request/{item}" for item in schema_errors(request, load_schema(root, REQUEST_SCHEMA)))
            if request.get("request_id") != deterministic_request_id(request):
                failures.append("request/request_id: deterministic identity mismatch")
            if sha256(request_raw) != manifest["request_ref"]["sha256"]:
                failures.append("request_ref/sha256: request bytes do not match")
            adapter_data, authorities = load_registries(root)
            profile = source_profile(request, adapter_data, authorities)
            bound_profile = profile
            validate_profile_url(request["url"], profile)
            if request["request_id"] != manifest["request_ref"]["request_id"]:
                failures.append("request_ref/request_id: request identity does not match")
            if request["source_class"] != manifest["source"]["source_class"] or request["profile_id"] != manifest["source"]["profile_id"] or request["url"] != manifest["source"]["requested_url"]:
                failures.append("source: manifest does not match request")
            expected_config = sha256(canonical_json(adapter_config(request)))
            if manifest["adapter"]["config_sha256"] != expected_config:
                failures.append("adapter/config_sha256: adapter configuration mismatch")
            if manifest["record_id"] != deterministic_record_id(request_raw, manifest["captured_utc"]):
                failures.append("record_id: deterministic identity mismatch")
        except (KeyError, OSError, UnicodeError, ValueError, StrictJSONError, CaptureBlocked):
            failures.append("request: cannot validate bound request")
    else:
        failures.append("artifacts: capture-request role is required")

    final_url = manifest.get("source", {}).get("final_url")
    final_verified = manifest.get("policy", {}).get("final_url_profile_verified")
    if (final_url is None) != (final_verified is False):
        failures.append("source/final_url: final URL and verification receipt disagree")
    if isinstance(final_url, str) and bound_profile is not None:
        try:
            validate_profile_url(final_url, bound_profile)
        except CaptureBlocked:
            failures.append("source/final_url: URL is outside the bound profile")

    if bound_request is not None and bound_profile is not None:
        policy = manifest.get("policy", {})
        robots_url = expected_robots_url(bound_request["url"])
        if policy.get("robots_url") != robots_url:
            failures.append("policy/robots_url: URL does not match the request origin")
        robots_raw = role_bytes.get("robots-policy")
        if robots_raw is None:
            if policy.get("robots_sha256") is not None or policy.get("robots_bytes") is not None:
                failures.append("policy/robots_sha256: receipt lacks a bound robots artifact")
        else:
            if (
                policy.get("robots_sha256") != sha256(robots_raw)
                or policy.get("robots_bytes") != len(robots_raw)
            ):
                failures.append("policy/robots_sha256: robots receipt identity mismatch")
        if policy.get("robots_status") == "allowed":
            if robots_raw is None:
                failures.append("policy/robots_status: allowed status lacks robots evidence")
            else:
                parser = RobotFileParser()
                parser.set_url(robots_url)
                parser.parse(robots_raw.decode("utf-8", errors="replace").splitlines())
                delay = parser.crawl_delay(USER_AGENT) or parser.crawl_delay("*") or 0
                if not parser.can_fetch(USER_AGENT, bound_request["url"]):
                    failures.append("policy/robots_status: bound policy does not allow the request")
                elif not isinstance(delay, (int, float)) or delay < 0 or delay > 60:
                    failures.append("policy/minimum_delay_seconds: invalid robots crawl delay")
                elif policy.get("minimum_delay_seconds") != max(
                    int(bound_profile["minimum_delay_seconds"]), int(delay)
                ):
                    failures.append("policy/minimum_delay_seconds: delay receipt mismatch")
    if manifest.get("status") == "success":
        required = {"capture-request", "robots-policy", "rendered-dom", "readable-markdown"}
        if not required.issubset(roles):
            failures.append("artifacts: successful capture lacks required roles")
        elif bound_request is not None:
            try:
                rendered = role_paths["rendered-dom"].read_text(encoding="utf-8")
                markdown = role_paths["readable-markdown"].read_text(encoding="utf-8")
                if not content_gate_passes(bound_request, rendered, markdown):
                    failures.append("result/content_gate_passed: content gate does not pass")
            except (OSError, UnicodeError, KeyError):
                failures.append("result/content_gate_passed: cannot replay content gate")
        http_status = manifest.get("result", {}).get("http_status")
        if not isinstance(http_status, int) or not 200 <= http_status <= 299:
            failures.append("result/http_status: successful capture requires HTTP 2xx")
    return failures


def plan_request(args: argparse.Namespace, root: Path) -> dict[str, Any]:
    adapter_data, authorities = load_registries(root)
    request = {
        "schema_version": "1.0",
        "contract_name": "web-source-capture-request",
        "created_utc": utc_now(),
        "source_class": args.source_class,
        "profile_id": args.profile_id,
        "url": args.url,
        "adapter_id": ADAPTER_ID,
        "native_route": {
            "fallback_condition": args.fallback_condition,
            "evidence": args.native_evidence,
        },
        "content_gate": {
            "required_css_selectors": args.require_css,
            "required_markdown_substrings": args.require_text,
            "forbidden_markdown_substrings": args.forbid_text,
            "minimum_markdown_bytes": args.minimum_markdown_bytes,
        },
        "limits": {
            "max_pages": 1,
            "max_depth": 0,
            "page_timeout_ms": args.page_timeout_ms,
            "max_artifact_bytes": 16777216,
        },
        "controls": {
            "check_robots_txt": True,
            "public_network_only": True,
            "allow_credentials": False,
            "allow_cookie_input": False,
            "allow_proxy": False,
            "allow_stealth": False,
            "allow_custom_javascript": False,
            "allow_llm_extraction": False,
            "capture_screenshot": False,
            "allow_deep_crawl": False,
            "allow_cache_reuse": False,
        },
    }
    request["request_id"] = deterministic_request_id(request)
    validate_profile_url(args.url, source_profile(request, adapter_data, authorities))
    failures = schema_errors(request, load_schema(root, REQUEST_SCHEMA))
    if failures:
        raise CaptureBlocked("REQUEST_SCHEMA_INVALID")
    return request


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root())
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan", help="Create a bounded capture request")
    plan.add_argument("--source-class", required=True, choices=("official-software", "official-package", "public-community"))
    plan.add_argument("--profile-id", required=True)
    plan.add_argument("--url", required=True)
    plan.add_argument("--fallback-condition", required=True, choices=("javascript-required", "browser-render-required", "native-response-incomplete"))
    plan.add_argument("--native-evidence", required=True)
    plan.add_argument("--require-css", action="append", default=[])
    plan.add_argument("--require-text", action="append", default=[])
    plan.add_argument("--forbid-text", action="append", default=[])
    plan.add_argument("--minimum-markdown-bytes", type=int, default=200)
    plan.add_argument("--page-timeout-ms", type=int, default=45000)
    plan.add_argument("--out", type=Path, required=True)

    capture = subparsers.add_parser("capture", help="Run one registered browser capture")
    capture.add_argument("--request", type=Path, required=True)
    capture.add_argument("--output-dir", type=Path, required=True)

    validate = subparsers.add_parser("validate", help="Validate a capture and all artifact hashes")
    validate.add_argument("--manifest", type=Path, required=True)
    validate.add_argument("--artifact-root", type=Path, required=True)

    subparsers.add_parser("check-runtime", help="Check the exact optional Crawl4AI runtime")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    try:
        if args.command == "check-runtime":
            print(f"PASS: Crawl4AI {runtime_version()} matches the registered adapter")
            return 0
        if args.command == "plan":
            try:
                ensure_output_scope(args.out, root)
            except CaptureBlocked as exc:
                if exc.code == "OUTPUT_ALREADY_EXISTS":
                    raise CaptureBlocked("PLAN_OUTPUT_ALREADY_EXISTS") from exc
                raise
            request = plan_request(args, root)
            args.out.write_bytes(canonical_json(request))
            print(f"PASS: wrote {REQUEST_INTERFACE} {request['request_id']}")
            return 0
        if args.command == "capture":
            status, manifest = run_capture(args.request, args.output_dir, root)
            print(
                f"{manifest['status'].upper()}: {MANIFEST_INTERFACE} "
                f"{manifest['record_id']} error={manifest['result']['error_code']}"
            )
            return status
        failures = validate_capture(args.manifest, args.artifact_root, root)
        if failures:
            for failure in failures:
                print(failure, file=sys.stderr)
            return 2
        print(f"PASS: {MANIFEST_INTERFACE} artifact and request identities verified")
        return 0
    except CaptureBlocked as exc:
        print(f"BLOCKED: {exc.code}", file=sys.stderr)
        return 3
    except (OSError, UnicodeError, ValueError, StrictJSONError) as exc:
        print(f"FAIL: {exc.__class__.__name__}", file=sys.stderr)
        return 2
    except CaptureFailed as exc:
        print(f"FAIL: {exc.code}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
