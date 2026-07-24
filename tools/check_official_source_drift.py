#!/usr/bin/env python3
"""Discover live official-source identity drift without mutating trust records.

This is an independent network lane.  It compares only exact tag, commit,
revision, ETag, and content-SHA-256 identities.  Network failure, missing
headers, and an absent baseline remain unavailable or unbaselined; they are
never relabeled as drift.  The tool writes only stdout or an explicit report
path outside canonical registries and official-source packs.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
)

import official_source_authorities
from registry_yaml import load_yaml_strict
import strict_json


SCHEMA_VERSION = "1.0"
REPORT_TYPE = "official-source-live-drift"
DRIFT_FIELDS = ("tag", "commit", "revid", "etag", "content_sha256")
IDENTITY_FIELDS = ("tag", "commit", "revid")
COMMIT_RE = re.compile(r"^[a-f0-9]{40}(?:[a-f0-9]{24})?$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
UTC_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)
MAX_REPORT_BYTES = 64 * 1024 * 1024
DEFAULT_MAX_CONTENT_BYTES = 8 * 1024 * 1024


class DriftError(ValueError):
    """One fail-closed live-drift input or output-boundary error."""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _origin(url: str) -> str | None:
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 443}
    ):
        return None
    return f"https://{parsed.hostname.lower()}" + (":443" if port == 443 else "")


def exact_locator_identity(url: str) -> dict[str, str | None]:
    """Extract only explicitly encoded tag, commit, and revision locators."""

    try:
        parsed = urlsplit(url)
    except ValueError:
        return {"tag": None, "commit": None, "revid": None}
    segments = tuple(segment for segment in parsed.path.split("/") if segment)
    commit = next(
        (segment for segment in segments if COMMIT_RE.fullmatch(segment)),
        None,
    )
    tag: str | None = None
    for marker in ("tag", "tags"):
        if marker in segments:
            index = segments.index(marker)
            if index + 1 < len(segments):
                tag = segments[index + 1]
                break
    if tag is None and len(segments) >= 3:
        for index in range(len(segments) - 2):
            if (
                segments[index] == "releases"
                and segments[index + 1] == "download"
            ):
                tag = segments[index + 2]
                break
    query = parse_qs(parsed.query, keep_blank_values=False)
    revid_values = query.get("oldid") or query.get("revid") or []
    revid = revid_values[0] if len(revid_values) == 1 else None
    if revid is None:
        for marker in ("revision", "revid"):
            if marker in segments:
                index = segments.index(marker)
                if index + 1 < len(segments):
                    revid = segments[index + 1]
                    break
    return {"tag": tag, "commit": commit, "revid": revid}


class _RestrictedRedirectHandler(HTTPRedirectHandler):
    def __init__(self, allowed_origins: tuple[str, ...]) -> None:
        super().__init__()
        self.allowed_origins = frozenset(allowed_origins)

    def redirect_request(  # type: ignore[override]
        self,
        request: Request,
        file_pointer: object,
        code: int,
        message: str,
        headers: object,
        new_url: str,
    ) -> Request | None:
        if _origin(new_url) not in self.allowed_origins:
            raise DriftError("redirect-origin-blocked")
        return super().redirect_request(
            request,
            file_pointer,
            code,
            message,
            headers,
            new_url,
        )


def _safe_etag(value: object) -> str | None:
    if value is None:
        return None
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 1000
        or not value.isprintable()
    ):
        return None
    return value


def fetch_url(
    url: str,
    allowed_origins: tuple[str, ...],
    *,
    timeout: float = 20.0,
    max_bytes: int = DEFAULT_MAX_CONTENT_BYTES,
) -> dict[str, object]:
    """Fetch one bounded HTTPS locator while keeping errors machine-stable."""

    if (
        not isinstance(timeout, (int, float))
        or isinstance(timeout, bool)
        or timeout <= 0
        or timeout > 120
    ):
        raise DriftError("timeout must be in (0, 120]")
    if (
        not isinstance(max_bytes, int)
        or isinstance(max_bytes, bool)
        or max_bytes <= 0
        or max_bytes > 128 * 1024 * 1024
    ):
        raise DriftError("max_bytes must be a bounded positive integer")
    if _origin(url) not in frozenset(allowed_origins):
        raise DriftError("locator origin is outside authority policy")
    request = Request(
        url,
        headers={
            "Accept": "*/*",
            "Accept-Encoding": "identity",
            "User-Agent": "Vibe-DFT-Skills-official-source-drift/1.0",
        },
        method="GET",
    )
    opener = build_opener(_RestrictedRedirectHandler(allowed_origins))
    try:
        with opener.open(request, timeout=float(timeout)) as response:
            final_url = response.geturl()
            if _origin(final_url) not in frozenset(allowed_origins):
                return {
                    "byte_count": None,
                    "content_sha256": None,
                    "error_code": "redirect-origin-blocked",
                    "etag": None,
                    "final_url": final_url,
                    "state": "unavailable",
                    "status_code": None,
                }
            status = getattr(response, "status", None)
            if not isinstance(status, int):
                status = response.getcode()
            etag = _safe_etag(response.headers.get("ETag"))
            declared_length = response.headers.get("Content-Length")
            if (
                isinstance(declared_length, str)
                and declared_length.isdigit()
                and int(declared_length) > max_bytes
            ):
                return {
                    "byte_count": None,
                    "content_sha256": None,
                    "error_code": "content-size-limit",
                    "etag": etag,
                    "final_url": final_url,
                    "state": "too-large",
                    "status_code": status,
                }
            digest = hashlib.sha256()
            count = 0
            while True:
                chunk = response.read(min(1024 * 1024, max_bytes + 1 - count))
                if not chunk:
                    break
                count += len(chunk)
                if count > max_bytes:
                    return {
                        "byte_count": None,
                        "content_sha256": None,
                        "error_code": "content-size-limit",
                        "etag": etag,
                        "final_url": final_url,
                        "state": "too-large",
                        "status_code": status,
                    }
                digest.update(chunk)
            return {
                "byte_count": count,
                "content_sha256": digest.hexdigest(),
                "error_code": None,
                "etag": etag,
                "final_url": final_url,
                "state": "retrieved",
                "status_code": status,
            }
    except HTTPError as exc:
        return {
            "byte_count": None,
            "content_sha256": None,
            "error_code": f"http-{exc.code}",
            "etag": _safe_etag(exc.headers.get("ETag") if exc.headers else None),
            "final_url": exc.geturl(),
            "state": "unavailable",
            "status_code": exc.code,
        }
    except DriftError as exc:
        return {
            "byte_count": None,
            "content_sha256": None,
            "error_code": str(exc),
            "etag": None,
            "final_url": url,
            "state": "unavailable",
            "status_code": None,
        }
    except (OSError, TimeoutError, URLError):
        return {
            "byte_count": None,
            "content_sha256": None,
            "error_code": "network-unavailable",
            "etag": None,
            "final_url": url,
            "state": "unavailable",
            "status_code": None,
        }


def _validate_retrieval(value: object, url: str) -> dict[str, object]:
    fields = {
        "byte_count",
        "content_sha256",
        "error_code",
        "etag",
        "final_url",
        "state",
        "status_code",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise DriftError("fetcher returned unsupported fields")
    state = value.get("state")
    if state not in {"retrieved", "too-large", "unavailable"}:
        raise DriftError("fetcher returned an unsupported state")
    final_url = value.get("final_url")
    if not isinstance(final_url, str) or _origin(final_url) is None:
        raise DriftError("fetcher returned an invalid final URL")
    status = value.get("status_code")
    if status is not None and (
        not isinstance(status, int)
        or isinstance(status, bool)
        or status < 100
        or status > 599
    ):
        raise DriftError("fetcher returned an invalid HTTP status")
    byte_count = value.get("byte_count")
    digest = value.get("content_sha256")
    if state == "retrieved":
        if (
            not isinstance(byte_count, int)
            or isinstance(byte_count, bool)
            or byte_count < 0
            or SHA256_RE.fullmatch(str(digest)) is None
        ):
            raise DriftError("retrieved content identity is incomplete")
        if value.get("error_code") is not None:
            raise DriftError("retrieved result cannot carry an error code")
    else:
        if byte_count is not None or digest is not None:
            raise DriftError("unavailable content must not claim a content hash")
        error = value.get("error_code")
        if not isinstance(error, str) or not error or not error.isprintable():
            raise DriftError("unavailable result requires a stable error code")
    etag = _safe_etag(value.get("etag"))
    if value.get("etag") is not None and etag is None:
        raise DriftError("fetcher returned an invalid ETag")
    return {
        **value,
        "etag": etag,
        "final_identity": exact_locator_identity(final_url),
    }


def _observation_key(observation: Mapping[str, Any]) -> tuple[str, str]:
    authority_id = observation.get("authority_id")
    url = observation.get("url")
    if not isinstance(authority_id, str) or not isinstance(url, str):
        raise DriftError("observation identity is invalid")
    return authority_id, url


def compare_observation(
    current: Mapping[str, Any],
    baseline: Mapping[str, Any] | None,
) -> dict[str, object]:
    """Compare exact identities only; missing evidence is never drift."""

    registered = current.get("registered_identity")
    retrieval = current.get("retrieval")
    if not isinstance(registered, dict) or not isinstance(retrieval, dict):
        raise DriftError("current observation is malformed")
    final_identity = retrieval.get("final_identity")
    if not isinstance(final_identity, dict):
        raise DriftError("current retrieval identity is malformed")
    changed: set[str] = set()
    comparable = False

    # A redirect away from an exact registered locator is live drift even on
    # the first run.  Null registered fields make no positive identity claim.
    for field in IDENTITY_FIELDS:
        registered_value = registered.get(field)
        if registered_value is not None:
            comparable = True
            if final_identity.get(field) != registered_value:
                changed.add(field)

    if baseline is not None:
        baseline_registered = baseline.get("registered_identity")
        baseline_retrieval = baseline.get("retrieval")
        if not isinstance(baseline_registered, dict) or not isinstance(
            baseline_retrieval, dict
        ):
            raise DriftError("baseline observation is malformed")
        for field in IDENTITY_FIELDS:
            old = baseline_registered.get(field)
            new = registered.get(field)
            if old is not None or new is not None:
                comparable = True
                if old != new:
                    changed.add(field)
        for field in ("etag", "content_sha256"):
            old = baseline_retrieval.get(field)
            new = retrieval.get(field)
            if isinstance(old, str) and isinstance(new, str):
                comparable = True
                if old != new:
                    changed.add(field)

    ordered = [field for field in DRIFT_FIELDS if field in changed]
    if ordered:
        state = "drifted"
    elif retrieval.get("state") == "unavailable":
        state = "unavailable"
    elif baseline is None:
        state = "unbaselined"
    elif comparable:
        state = "unchanged"
    else:
        state = "unavailable"
    return {"drift_fields": ordered, "state": state}


def _baseline_index(
    report: Mapping[str, Any] | None,
) -> dict[tuple[str, str], Mapping[str, Any]]:
    if report is None:
        return {}
    if (
        report.get("schema_version") != SCHEMA_VERSION
        or report.get("report_type") != REPORT_TYPE
    ):
        raise DriftError("baseline report identity is invalid")
    observations = report.get("observations")
    if not isinstance(observations, list):
        raise DriftError("baseline observations must be a list")
    result: dict[tuple[str, str], Mapping[str, Any]] = {}
    for observation in observations:
        if not isinstance(observation, dict):
            raise DriftError("baseline observation is invalid")
        key = _observation_key(observation)
        if key in result:
            raise DriftError("baseline observation identity is duplicated")
        result[key] = observation
    return result


def _validate_timestamp(value: str) -> None:
    if UTC_RE.fullmatch(value) is None:
        raise DriftError("observed_utc must be a whole-second UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DriftError("observed_utc is invalid") from exc
    if parsed.tzinfo != timezone.utc:
        raise DriftError("observed_utc must be UTC")


def _snapshot_projection(value: object) -> dict[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise DriftError("canonical snapshot projection is invalid")
    snapshot_id = value.get("snapshot_id")
    digest = value.get("manifest_raw_sha256")
    if (
        not isinstance(snapshot_id, str)
        or not snapshot_id
        or SHA256_RE.fullmatch(str(digest)) is None
    ):
        raise DriftError("canonical snapshot exact identity is invalid")
    return {
        "manifest_raw_sha256": str(digest),
        "snapshot_id": snapshot_id,
    }


def build_report_from_authorities(
    authorities: Mapping[str, Mapping[str, Any]],
    *,
    registry_sha256: str,
    observed_utc: str,
    fetcher: Callable[[str, tuple[str, ...]], Mapping[str, object]],
    baseline_report: Mapping[str, Any] | None = None,
    baseline_report_sha256: str | None = None,
) -> dict[str, object]:
    _validate_timestamp(observed_utc)
    if SHA256_RE.fullmatch(registry_sha256) is None:
        raise DriftError("authority registry digest is invalid")
    if baseline_report_sha256 is not None and SHA256_RE.fullmatch(
        baseline_report_sha256
    ) is None:
        raise DriftError("baseline report digest is invalid")
    baseline = _baseline_index(baseline_report)
    observations: list[dict[str, object]] = []
    for authority_id, authority in sorted(authorities.items()):
        provider_id = authority.get("provider_id")
        urls = authority.get("canonical_urls")
        probe_urls = authority.get("probe_urls", urls)
        scopes = authority.get("version_scopes")
        if (
            not isinstance(authority_id, str)
            or not isinstance(provider_id, str)
            or not isinstance(urls, list)
            or not urls
            or not all(isinstance(url, str) for url in urls)
            or not isinstance(probe_urls, list)
            or not probe_urls
            or not all(isinstance(url, str) for url in probe_urls)
            or not isinstance(scopes, list)
        ):
            raise DriftError(f"{authority_id}: authority projection is invalid")
        configured_origins = authority.get("allowed_https_origins")
        if configured_origins is None:
            origins = tuple(
                sorted({_origin(url) for url in urls if _origin(url) is not None})
            )
        elif (
            isinstance(configured_origins, list)
            and all(isinstance(item, str) for item in configured_origins)
        ):
            origins = tuple(sorted(configured_origins))
        else:
            raise DriftError(f"{authority_id}: allowed origins are invalid")
        snapshot = _snapshot_projection(authority.get("canonical_snapshot"))
        for url in sorted(probe_urls):
            fetched = _validate_retrieval(dict(fetcher(url, origins)), url)
            observation: dict[str, object] = {
                "authority_id": authority_id,
                "provider_id": provider_id,
                "registered_identity": exact_locator_identity(url),
                "registered_snapshot": snapshot,
                "registered_version_scopes": scopes,
                "retrieval": fetched,
                "url": url,
            }
            comparison = compare_observation(
                observation,
                baseline.get((authority_id, url)),
            )
            observation["comparison"] = comparison
            observations.append(observation)
    observations.sort(key=lambda item: (str(item["authority_id"]), str(item["url"])))
    states = ("drifted", "unchanged", "unavailable", "unbaselined")
    summary = {
        state: sum(
            item["comparison"]["state"] == state  # type: ignore[index]
            for item in observations
        )
        for state in states
    }
    summary["total"] = len(observations)
    return {
        "authority_registry_sha256": registry_sha256,
        "baseline_report_sha256": baseline_report_sha256,
        "comparison_policy": {
            "drift_fields": list(DRIFT_FIELDS),
            "missing_evidence": "unavailable-not-drift",
            "redirect_identity": "compare-exact-registered-locator",
        },
        "mutation_policy": {
            "official_source_packs": "never-auto-edit",
            "registries": "never-auto-edit",
        },
        "network_lane": "independent-scheduled-live-discovery",
        "observations": observations,
        "observed_utc": observed_utc,
        "report_type": REPORT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "summary": summary,
    }


def _load_authorities(
    root: Path,
) -> tuple[dict[str, dict[str, Any]], str]:
    registry_path = root / "registry" / "official-source-authorities.yaml"
    try:
        raw = registry_path.read_bytes()
        authority_data = official_source_authorities.load_registry(registry_path)
        software_data = load_yaml_strict(
            root / "registry" / "software-registry.yaml",
            "software-registry.yaml",
        )
        projection = official_source_authorities.active_authority_snapshot(
            authority_data,
            software_data=software_data,
            source_root=root,
        )
    except (OSError, ValueError) as exc:
        raise DriftError(f"official-source authority registry is invalid ({exc})") from exc
    raw_authorities = authority_data.get("authorities")
    if not isinstance(raw_authorities, dict):
        raise DriftError("official-source authorities mapping is invalid")
    for authority_id, authority in projection.items():
        origins = frozenset(authority["allowed_https_origins"])
        prefixes = tuple(authority["allowed_path_prefixes"])
        concrete: list[str] = []
        raw_entry = raw_authorities.get(authority_id)
        provenance = (
            raw_entry.get("provenance")
            if isinstance(raw_entry, dict)
            else None
        )
        fact_urls = (
            provenance.get("official_fact_urls")
            if isinstance(provenance, dict)
            else []
        )
        candidates = [
            *authority.get("license_terms_urls", []),
            *(fact_urls if isinstance(fact_urls, list) else []),
        ]
        for url in candidates:
            if not isinstance(url, str):
                continue
            try:
                parsed = urlsplit(url)
            except ValueError:
                continue
            if _origin(url) in origins and any(
                parsed.path.startswith(prefix) for prefix in prefixes
            ):
                concrete.append(url)
        authority["probe_urls"] = sorted(
            set(concrete or authority["canonical_urls"])
        )
    return projection, _sha256(raw)


def _load_baseline(path: Path | None) -> tuple[dict[str, Any] | None, str | None]:
    if path is None:
        return None, None
    try:
        raw = path.read_bytes()
        report = strict_json.loads_value(
            raw,
            path.name,
            max_bytes=MAX_REPORT_BYTES,
            max_nodes=1_000_000,
            max_depth=128,
            max_string_chars=8 * 1024 * 1024,
        )
    except (OSError, strict_json.StrictJSONError) as exc:
        raise DriftError(f"baseline report is invalid ({exc})") from exc
    if not isinstance(report, dict):
        raise DriftError("baseline report root must be an object")
    _baseline_index(report)
    return report, _sha256(raw)


def build_report(
    root: Path,
    *,
    observed_utc: str,
    baseline_path: Path | None = None,
    timeout: float = 20.0,
    max_bytes: int = DEFAULT_MAX_CONTENT_BYTES,
) -> dict[str, object]:
    try:
        selected_root = Path(root).resolve(strict=True)
    except OSError as exc:
        raise DriftError(
            f"repository root is unavailable ({exc.__class__.__name__})"
        ) from exc
    authorities, registry_digest = _load_authorities(selected_root)
    baseline, baseline_digest = _load_baseline(baseline_path)

    def fetcher(url: str, origins: tuple[str, ...]) -> Mapping[str, object]:
        return fetch_url(
            url,
            origins,
            timeout=timeout,
            max_bytes=max_bytes,
        )

    return build_report_from_authorities(
        authorities,
        registry_sha256=registry_digest,
        observed_utc=observed_utc,
        fetcher=fetcher,
        baseline_report=baseline,
        baseline_report_sha256=baseline_digest,
    )


def report_bytes(report: Mapping[str, object]) -> bytes:
    return (
        json.dumps(
            report,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def validate_output_path(root: Path, output: Path) -> Path:
    """Reject the two trust locations this live lane must never mutate."""

    selected_root = Path(root).resolve(strict=True)
    selected_output = Path(output).resolve(strict=False)
    registry_root = selected_root / "registry"
    try:
        selected_output.relative_to(registry_root)
    except ValueError:
        pass
    else:
        raise DriftError("live drift reports must not write registry paths")
    try:
        relative = selected_output.relative_to(selected_root)
    except ValueError:
        return selected_output
    parts = PurePosixPath(relative.as_posix()).parts
    if (
        len(parts) >= 5
        and parts[0] == "skills"
        and parts[2] == "references"
        and parts[3] == "official-source-pack"
    ):
        raise DriftError("live drift reports must not write official-source packs")
    return selected_output


def _write_report(path: Path, raw: bytes, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise DriftError(f"output already exists: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(raw)
        if path.exists() and not overwrite:
            raise DriftError(f"output appeared during write: {path.name}")
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root())
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_CONTENT_BYTES)
    parser.add_argument("--observed-at", default=None)
    parser.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="optional manual gate; scheduled default remains report-only",
    )
    args = parser.parse_args(argv)
    try:
        report = build_report(
            args.root,
            observed_utc=args.observed_at or _utc_now(),
            baseline_path=args.baseline,
            timeout=args.timeout,
            max_bytes=args.max_bytes,
        )
        raw = report_bytes(report)
        if args.output is None:
            sys.stdout.buffer.write(raw)
        else:
            output = validate_output_path(args.root, args.output)
            _write_report(output, raw, overwrite=args.force)
            summary = report["summary"]
            assert isinstance(summary, dict)
            print(
                "OFFICIAL_SOURCE_DRIFT "
                f"total={summary['total']} drifted={summary['drifted']} "
                f"unavailable={summary['unavailable']} "
                f"unbaselined={summary['unbaselined']} output={output}"
            )
        if args.fail_on_drift and report["summary"]["drifted"]:  # type: ignore[index]
            return 3
    except (DriftError, OSError, ValueError) as exc:
        print(f"ERROR OFFICIAL_SOURCE_DRIFT {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
