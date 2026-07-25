#!/usr/bin/env python3
"""Materialize registered official documents as local, readable Markdown.

The repository's official-document packs intentionally retain metadata and
receipts rather than redistributing third-party document bodies.  This tool
uses those exact receipts to build a local-only cache, scoped by consumer
Skill.  It never changes an authority, widens a URL allowlist, or treats a
successful conversion as scientific validation.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from typing import Any
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlsplit
from urllib.request import Request, urlopen

from registry_yaml import load_yaml_strict


SCHEMA_VERSION = "1.0"
USER_AGENT = "Vibe-DFT-Skills-official-manual-cache/1.0"
MAX_DOWNLOAD_BYTES = 96 * 1024 * 1024
_GITHUB_API_HAS_CAPACITY: bool | None = None
TRACKED_MIRRORS = {
    "cp2k-official-manual": (
        "skills/cp2k-rigorous-calculations/references/official-manual",
        "*.md",
    ),
    "qe-official-docs": (
        "skills/qe-rigorous-calculations/references",
        "official-*.md",
    ),
    "vasp-official-wiki": (
        "skills/vasp-rigorous-calculations/references/official-wiki",
        "*.md",
    ),
}
TEXT_SUFFIXES = {
    "",
    ".cfg",
    ".dic",
    ".f",
    ".f90",
    ".js",
    ".md",
    ".php",
    ".py",
    ".rst",
    ".tex",
    ".txt",
    ".xml",
}
MANUAL_TREE_SUFFIXES = {
    "",
    ".1",
    ".1b",
    ".3",
    ".5",
    ".7",
    ".7b",
    ".cfg",
    ".dic",
    ".html",
    ".htm",
    ".md",
    ".rst",
    ".tex",
    ".txt",
}
BODY_SOURCE_KINDS = {
    "api-record",
    "guide",
    "manual",
    "manual-page",
    "reference-page",
    "source-documentation",
}


class CacheError(RuntimeError):
    """One stable, user-readable cache failure."""


class TextExtractor(HTMLParser):
    """Extract visible-ish source text for conversion quality checks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self.ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self.ignored_depth:
            self.ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.ignored_depth:
            self.parts.append(data)


@dataclass(frozen=True)
class SourceRecord:
    skill_id: str
    authority_id: str
    source_id: str
    title: str
    source_kind: str
    locator: str
    retrieval_method: str
    raw_bytes: int
    raw_sha256: str


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def safe_component(value: str) -> str:
    result = re.sub(r"[^a-z0-9._-]+", "-", value.lower()).strip(".-")
    if not result or result in {".", ".."}:
        raise CacheError("unsafe empty cache path component")
    return result[:180]


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CacheError(f"cannot read JSON: {path}") from exc
    if not isinstance(value, dict):
        raise CacheError(f"expected JSON object: {path}")
    return value


def discover_records(root: Path) -> tuple[SourceRecord, ...]:
    corpus_authorities: dict[tuple[str, str], str] = {}
    source_metadata: dict[tuple[str, str, str], tuple[str, str]] = {}
    for path in sorted(root.glob("skills/*/references/official-source-pack/corpus-*.json")):
        data = load_json(path)
        skill_id = path.parts[-4]
        corpus_id = data.get("corpus_id")
        authority_id = data.get("authority_id")
        if isinstance(corpus_id, str) and isinstance(authority_id, str):
            corpus_authorities[(skill_id, corpus_id)] = authority_id
            inventory = data.get("source_inventory")
            if isinstance(inventory, dict):
                for source_id, source in inventory.items():
                    if not isinstance(source_id, str) or not isinstance(source, dict):
                        continue
                    source_kind = source.get("source_kind", "unknown")
                    title = source.get("title", source_id)
                    source_metadata[(skill_id, corpus_id, source_id)] = (
                        source_kind if isinstance(source_kind, str) else "unknown",
                        title if isinstance(title, str) else source_id,
                    )

    records: dict[tuple[str, str, str], SourceRecord] = {}
    for path in sorted(root.glob("skills/*/references/official-source-pack/slices-*.json")):
        data = load_json(path)
        skill_id = path.parts[-4]
        corpus_ref = data.get("corpus_ref")
        if not isinstance(corpus_ref, dict) or not isinstance(corpus_ref.get("corpus_id"), str):
            raise CacheError(f"missing corpus_ref: {path}")
        authority_id = corpus_authorities.get((skill_id, corpus_ref["corpus_id"]))
        if authority_id is None:
            raise CacheError(f"unknown corpus authority: {path}")
        sources = data.get("sources")
        if not isinstance(sources, dict):
            raise CacheError(f"missing sources mapping: {path}")
        for source_id, source in sources.items():
            if not isinstance(source_id, str) or not isinstance(source, dict):
                raise CacheError(f"malformed source: {path}")
            identity = source.get("source_identity")
            slices = source.get("slices")
            if not isinstance(identity, dict) or not isinstance(slices, list):
                raise CacheError(f"malformed source identity: {path}:{source_id}")
            receipt = identity.get("receipt")
            if not isinstance(receipt, dict):
                raise CacheError(f"missing source receipt: {path}:{source_id}")
            locator = identity.get("locator")
            raw_bytes = receipt.get("raw_bytes")
            raw_sha256 = receipt.get("raw_sha256")
            method = receipt.get("retrieval_method")
            if (
                not isinstance(locator, str)
                or not isinstance(raw_bytes, int)
                or raw_bytes < 0
                or not isinstance(raw_sha256, str)
                or re.fullmatch(r"[a-f0-9]{64}", raw_sha256) is None
                or not isinstance(method, str)
            ):
                raise CacheError(f"invalid source receipt: {path}:{source_id}")
            source_kind, title = source_metadata.get(
                (skill_id, corpus_ref["corpus_id"], source_id),
                ("unknown", source_id),
            )
            record = SourceRecord(
                skill_id=skill_id,
                authority_id=authority_id,
                source_id=source_id,
                title=title,
                source_kind=source_kind,
                locator=locator,
                retrieval_method=method,
                raw_bytes=raw_bytes,
                raw_sha256=raw_sha256,
            )
            key = (skill_id, authority_id, source_id)
            previous = records.get(key)
            if previous is not None and previous != record:
                raise CacheError(f"conflicting duplicate source: {key}")
            records[key] = record
    return tuple(records[key] for key in sorted(records))


def authority_allows(record: SourceRecord, authorities: dict[str, Any]) -> bool:
    authority = authorities.get(record.authority_id)
    if not isinstance(authority, dict) or authority.get("lifecycle") != "active":
        return False
    parsed = urlsplit(record.locator)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if parsed.scheme != "https" or origin not in authority.get("allowed_https_origins", []):
        return False
    policy = authority.get("content_policy")
    if not isinstance(policy, dict):
        return False
    if parsed.fragment and policy.get("fragment_policy") == "forbidden":
        return False
    if parsed.query:
        query_policy = policy.get("query_policy")
        allowed_queries = policy.get("allowed_query_urls", [])
        if query_policy == "forbidden" or record.locator not in allowed_queries:
            return False
    prefixes = policy.get("allowed_path_prefixes")
    return isinstance(prefixes, list) and any(parsed.path.startswith(prefix) for prefix in prefixes)


def retrieval_transport_url(locator: str) -> str:
    """Use the exact raw transport for pinned GitHub blob locators."""

    parsed = urlsplit(locator)
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc == "github.com" and len(parts) >= 5 and parts[2] == "blob":
        owner, repository, _, revision, *source_parts = parts
        return (
            f"https://raw.githubusercontent.com/{owner}/{repository}/{revision}/"
            f"{'/'.join(source_parts)}"
        )
    return locator


def github_blob_spec(locator: str) -> tuple[str, str, str] | None:
    parsed = urlsplit(locator)
    parts = [part for part in parsed.path.split("/") if part]
    if (
        parsed.netloc != "github.com"
        or len(parts) < 5
        or parts[2] != "blob"
        or re.fullmatch(r"[a-f0-9]{40}", parts[3]) is None
    ):
        return None
    return (
        f"https://github.com/{parts[0]}/{parts[1]}",
        parts[3],
        "/".join(parts[4:]),
    )


def pinned_github_file_spec(locator: str) -> tuple[str, str, str] | None:
    blob = github_blob_spec(locator)
    if blob is not None:
        return blob
    parsed = urlsplit(locator)
    parts = [part for part in parsed.path.split("/") if part]
    if (
        parsed.netloc != "raw.githubusercontent.com"
        or len(parts) < 4
        or re.fullmatch(r"[a-f0-9]{40}", parts[2]) is None
    ):
        return None
    return (
        f"https://github.com/{parts[0]}/{parts[1]}",
        parts[2],
        "/".join(parts[3:]),
    )


def github_api_raw_url(locator: str) -> str | None:
    specification = pinned_github_file_spec(locator)
    if specification is None:
        return None
    repository_url, commit_id, source_path = specification
    repository_parts = [part for part in urlsplit(repository_url).path.split("/") if part]
    owner, repository = repository_parts
    return (
        f"https://api.github.com/repos/{quote(owner, safe='')}/{quote(repository, safe='')}"
        f"/contents/{quote(source_path, safe='/')}?ref={commit_id}"
    )


def curl_fetch_bytes(
    curl: str,
    url: str,
    *,
    accept: str = "*/*",
) -> bytes | None:
    with tempfile.TemporaryDirectory(prefix="official-manual-curl-") as temporary:
        output = Path(temporary) / "body"
        result = subprocess.run(
            [
                curl,
                "--fail",
                "--location",
                "--silent",
                "--show-error",
                "--http1.1",
                "--header",
                f"User-Agent: {USER_AGENT}",
                "--header",
                f"Accept: {accept}",
                "--retry",
                "3",
                "--retry-all-errors",
                "--connect-timeout",
                "15",
                "--max-time",
                "180",
                "--output",
                str(output),
                url,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=240,
            check=False,
        )
        if result.returncode != 0 or not output.is_file():
            return None
        data = output.read_bytes()
        return data if len(data) <= MAX_DOWNLOAD_BYTES else None


def github_api_has_capacity(curl: str) -> bool:
    global _GITHUB_API_HAS_CAPACITY
    if _GITHUB_API_HAS_CAPACITY is not None:
        return _GITHUB_API_HAS_CAPACITY
    data = curl_fetch_bytes(
        curl,
        "https://api.github.com/rate_limit",
        accept="application/vnd.github+json",
    )
    try:
        value = json.loads(data.decode("utf-8")) if data is not None else {}
        remaining = value["resources"]["core"]["remaining"]
    except (KeyError, TypeError, UnicodeError, json.JSONDecodeError):
        remaining = 0
    _GITHUB_API_HAS_CAPACITY = isinstance(remaining, int) and remaining > 0
    return _GITHUB_API_HAS_CAPACITY


def fetch_bytes(
    record: SourceRecord,
    *,
    allow_live_drift: bool,
    retries: int = 3,
    fallback_repositories: tuple[tuple[str, str], ...] = (),
) -> tuple[bytes, str, str]:
    transport_url = retrieval_transport_url(record.locator)
    curl = shutil.which("curl")
    if curl:
        api_url = github_api_raw_url(record.locator)
        if api_url is not None:
            if github_api_has_capacity(curl):
                data = curl_fetch_bytes(
                    curl,
                    api_url,
                    accept="application/vnd.github.raw+json",
                )
                if (
                    data is not None
                    and len(data) == record.raw_bytes
                    and sha256_bytes(data) == record.raw_sha256
                ):
                    return data, "verified-registered-receipt-via-official-api", record.locator
                if data is not None and allow_live_drift:
                    return (
                        data,
                        "registered-receipt-mismatch-at-pinned-official-source",
                        record.locator,
                    )
            try:
                recovered = recover_registered_github_blob(record)
            except CacheError:
                recovered = None
            if recovered is not None:
                data, resolved_locator = recovered
                return data, "verified-registered-receipt-via-pinned-archive", resolved_locator
            if allow_live_drift:
                recovered = recover_pinned_github_path(record)
                if recovered is not None:
                    data, resolved_locator = recovered
                    return (
                        data,
                        "registered-receipt-mismatch-at-pinned-official-source",
                        resolved_locator,
                    )
        data = curl_fetch_bytes(curl, transport_url)
        if data is not None:
            if len(data) == record.raw_bytes and sha256_bytes(data) == record.raw_sha256:
                return data, "verified-registered-receipt", record.locator
            if allow_live_drift:
                return data, "drifted-live-official", record.locator
    request = Request(transport_url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"})
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urlopen(request, timeout=45) as response:
                data = response.read(MAX_DOWNLOAD_BYTES + 1)
            if len(data) > MAX_DOWNLOAD_BYTES:
                raise CacheError(f"download too large: {record.source_id}")
            if len(data) != record.raw_bytes or sha256_bytes(data) != record.raw_sha256:
                if allow_live_drift:
                    return data, "drifted-live-official", record.locator
                raise CacheError(
                    f"receipt mismatch: {record.skill_id}/{record.source_id} "
                    f"(expected {record.raw_bytes}:{record.raw_sha256}, "
                    f"got {len(data)}:{sha256_bytes(data)})"
                )
            return data, "verified-registered-receipt", record.locator
        except (HTTPError, URLError, TimeoutError, ConnectionError, OSError) as exc:
            last_error = exc
            if attempt + 1 < retries:
                if isinstance(exc, HTTPError) and exc.code == 429:
                    time.sleep(5 * (attempt + 1))
                else:
                    time.sleep(1.5 * (attempt + 1))
    try:
        recovered = recover_registered_github_blob(record)
    except CacheError:
        recovered = None
    if recovered is not None:
        data, resolved_locator = recovered
        return data, "verified-registered-receipt-via-pinned-archive", resolved_locator
    if allow_live_drift:
        recovered = recover_pinned_github_path(record)
        if recovered is not None:
            data, resolved_locator = recovered
            return (
                data,
                "registered-receipt-mismatch-at-pinned-official-source",
                resolved_locator,
            )
    recovered = recover_registered_receipt_from_repositories(
        record,
        fallback_repositories,
    )
    if recovered is not None:
        data, resolved_locator = recovered
        return data, "verified-registered-receipt-via-authority-repository", resolved_locator
    raise CacheError(f"retrieval failed: {record.skill_id}/{record.source_id}: {last_error}")


def decode_utf8(data: bytes, record: SourceRecord) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CacheError(f"source is not strict UTF-8: {record.skill_id}/{record.source_id}") from exc


def wp_rendered_html(text: str) -> str | None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    content = data.get("content")
    if isinstance(content, dict) and isinstance(content.get("rendered"), str):
        return content["rendered"]
    parsed = data.get("parse")
    if isinstance(parsed, dict) and isinstance(parsed.get("text"), str):
        return parsed["text"]
    return None


def run_html2md(html: str, executable: str) -> str:
    html = strip_noncontent_html(html)
    result = subprocess.run(
        [executable],
        input=html,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        check=False,
    )
    if result.returncode != 0:
        raise CacheError(f"html2md failed: {result.stderr.strip()}")
    markdown = result.stdout.replace("\r\n", "\n").replace("\r", "\n").strip() + "\n"
    if "\ufffd" in markdown:
        raise CacheError("html2md emitted a Unicode replacement character")
    extractor = TextExtractor()
    extractor.feed(html)
    source_text = " ".join(extractor.parts)
    source_tokens = re.findall(r"[\w\u0080-\U0010ffff]+", source_text, flags=re.UNICODE)
    markdown_tokens = re.findall(r"[\w\u0080-\U0010ffff]+", markdown, flags=re.UNICODE)
    if source_tokens and len(markdown_tokens) < max(1, len(source_tokens) // 5):
        raise CacheError("html2md output failed the minimum token-retention gate")
    source_non_ascii_letters = [
        char
        for char in source_text
        if ord(char) > 127 and unicodedata.category(char).startswith("L")
    ]
    markdown_non_ascii_letters = [
        char
        for char in markdown
        if ord(char) > 127 and unicodedata.category(char).startswith("L")
    ]
    if len(source_non_ascii_letters) >= 2 and not markdown_non_ascii_letters:
        raise CacheError("html2md dropped every non-ASCII letter")
    return markdown


def strip_noncontent_html(html: str) -> str:
    return re.sub(
        r"<(script|style|noscript)\b[^>]*>.*?</\1\s*>",
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )


def normalize_visible_controls(text: str) -> tuple[str, bool]:
    changed = False
    output: list[str] = []
    for character in text:
        codepoint = ord(character)
        if character in "\n\r\t" or unicodedata.category(character) != "Cc":
            output.append(character)
            continue
        changed = True
        if codepoint == 0x88:
            output.append("•")
        elif codepoint == 0x0C:
            output.append("\n\n<!-- source page break U+000C -->\n\n")
        else:
            output.append(f"⟦source-control-U+{codepoint:04X}⟧")
    return "".join(output), changed


def fenced_source(text: str, language: str) -> str:
    longest = max((len(match.group(0)) for match in re.finditer(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}{language}\n{text.rstrip()}\n{fence}\n"


def pretty_json_source(text: str) -> str | None:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return None
    return fenced_source(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True),
        "json",
    )


def pdf_to_markdown(data: bytes, pdftotext: str) -> str:
    with tempfile.TemporaryDirectory(prefix="official-manual-pdf-") as tmp:
        source = Path(tmp) / "source.pdf"
        target = Path(tmp) / "source.txt"
        source.write_bytes(data)
        result = subprocess.run(
            [pdftotext, "-layout", "-enc", "UTF-8", str(source), str(target)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=180,
            check=False,
        )
        if result.returncode != 0 or not target.is_file():
            raise CacheError(f"pdftotext failed: {result.stderr.decode('utf-8', 'replace').strip()}")
        text = target.read_text(encoding="utf-8")
    if "\ufffd" in text or not text.strip():
        raise CacheError("PDF extraction produced empty or replacement-character text")
    return fenced_source(text, "text")


def convert(record: SourceRecord, data: bytes, html2md: str, pdftotext: str) -> tuple[str, str]:
    suffix = Path(unquote(urlsplit(record.locator).path)).suffix.lower()
    if suffix == ".pdf":
        if data.startswith(b"%PDF-"):
            return pdf_to_markdown(data, pdftotext), "pdftotext-layout"
        text = decode_utf8(data, record)
        lower = text[:4096].lower()
        if "<html" in lower or "<!doctype html" in lower:
            return run_html2md(text, html2md), "html2md-pdf-endpoint-fallback"
        raise CacheError(f"PDF endpoint did not return a PDF: {record.skill_id}/{record.source_id}")
    text = decode_utf8(data, record)
    rendered = wp_rendered_html(text) if record.retrieval_method == "official-api" else None
    lower = text[:4096].lower()
    is_html = (
        rendered is not None
        or suffix in {".html", ".htm", ".php"}
        or "<html" in lower
        or "<main" in lower
        or "<article" in lower
    )
    if is_html:
        try:
            return run_html2md(rendered if rendered is not None else text, html2md), "html2md"
        except CacheError:
            if record.retrieval_method in {"verified-git-object", "pinned-official-archive"}:
                return fenced_source(text, "html"), "lossless-html-source-fence"
            raise
    pretty_json = pretty_json_source(text)
    if pretty_json is not None:
        return pretty_json, "pretty-json"
    if suffix == ".md":
        if "\ufffd" in text:
            raise CacheError("Markdown source contains a Unicode replacement character")
        return text.rstrip() + "\n", "identity-markdown"
    language = suffix.lstrip(".") if suffix in TEXT_SUFFIXES and suffix else "text"
    return fenced_source(text, language), "lossless-source-fence"


def provenance_header(
    record: SourceRecord,
    conversion: str,
    *,
    receipt_status: str = "verified-registered-receipt",
    actual_raw_bytes: int | None = None,
    actual_raw_sha256: str | None = None,
    resolved_locator: str | None = None,
) -> str:
    drift = ""
    if not receipt_status.startswith("verified-registered-receipt"):
        drift = (
            f"- Live receipt status: `{receipt_status}`\n"
            f"- Live raw identity: `{actual_raw_sha256}` ({actual_raw_bytes} bytes)\n"
            "- Claim gate: `blocked-for-version-sensitive-use-until-registry-refresh`\n"
        )
    resolution = ""
    if resolved_locator is not None and resolved_locator != record.locator:
        resolution = (
            f"- Resolved official source: <{resolved_locator}>\n"
            f"- Registered locator status: `stale-path-recovered-by-exact-receipt`\n"
        )
    return (
        f"# {record.title}\n\n"
        f"- Official source: <{record.locator}>\n"
        f"{resolution}"
        f"- Authority: `{record.authority_id}`\n"
        f"- Raw identity: `{record.raw_sha256}` ({record.raw_bytes} bytes)\n"
        f"- Retrieval method: `{record.retrieval_method}`\n"
        f"- Local conversion: `{conversion}`\n\n"
        f"{drift}"
        "> Local cache only. This derived Markdown is not a redistributed official manual, "
        "does not replace the official source, and does not establish scientific validity.\n\n"
    )


def tracked_files(root: Path, authority_id: str) -> tuple[Path, ...]:
    specification = TRACKED_MIRRORS.get(authority_id)
    if specification is None:
        return ()
    directory, pattern = specification
    return tuple(sorted((root / directory).glob(pattern)))


def inventory_for(root: Path, skill_id: str, authority_id: str) -> dict[str, Any] | None:
    matches: list[dict[str, Any]] = []
    for path in sorted(
        (root / "skills" / skill_id / "references").glob("source-pack-inventory-*.json")
    ):
        value = load_json(path)
        if value.get("authority_id") == authority_id and isinstance(value.get("entries"), list):
            matches.append(value)
    if len(matches) > 1:
        raise CacheError(f"multiple source-tree inventories: {skill_id}/{authority_id}")
    return matches[0] if matches else None


def git_run(argv: list[str], cwd: Path, *, timeout: int = 300) -> str:
    result = subprocess.run(
        ["git", *argv],
        cwd=cwd,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        raise CacheError(f"git {' '.join(argv[:2])} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def git_fetch_commit(repository_url: str, commit_id: str, checkout: Path) -> None:
    last_error: CacheError | None = None
    for attempt in range(3):
        try:
            git_run(
                [
                    "-c",
                    "http.version=HTTP/1.1",
                    "fetch",
                    "-q",
                    "--depth",
                    "1",
                    "--filter=blob:none",
                    "origin",
                    commit_id,
                ],
                checkout,
                timeout=600,
            )
            return
        except CacheError as exc:
            last_error = exc
            if attempt + 1 < 3:
                time.sleep(2 * (attempt + 1))
    raise CacheError(f"git fetch failed for {repository_url}: {last_error}")


def manual_tree_entry(path: str) -> bool:
    item = Path(path)
    suffix = item.suffix.lower()
    name = item.name.lower()
    if suffix not in MANUAL_TREE_SUFFIXES:
        return False
    if suffix == "" and not (
        name.startswith("readme")
        or name.startswith("manual")
        or re.fullmatch(r"[a-z0-9_.+-]+\\.[157](?:b)?", name)
    ):
        return False
    excluded_parts = {
        ".git",
        "_build",
        "_static",
        "assets",
        "css",
        "fig",
        "figs",
        "fonts",
        "images",
        "js",
        "templates",
    }
    return not any(part.lower() in excluded_parts for part in item.parts)


def git_blob_oid(data: bytes) -> str:
    prefix = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(prefix + data, usedforsecurity=False).hexdigest()


def archive_url(repository_url: str, commit_id: str) -> str | None:
    parsed = urlsplit(repository_url)
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc == "github.com" and len(parts) == 2:
        return f"https://codeload.github.com/{parts[0]}/{parts[1]}/tar.gz/{commit_id}"
    if parsed.netloc == "gitlab.com" and len(parts) >= 2:
        project = parts[-1]
        return (
            f"https://gitlab.com/{'/'.join(parts)}/-/archive/{commit_id}/"
            f"{project}-{commit_id}.tar.gz"
        )
    return None


def download_archive(url: str, output: Path) -> None:
    curl = shutil.which("curl")
    if not curl:
        raise CacheError("curl is required for exact source-tree archives")
    result = subprocess.run(
        [
            curl,
            "--fail",
            "--location",
            "--silent",
            "--show-error",
            "--http1.1",
            "--retry",
            "3",
            "--retry-all-errors",
            "--max-time",
            "600",
            "--output",
            str(output),
            url,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=660,
        check=False,
    )
    if result.returncode != 0 or not output.is_file():
        raise CacheError(f"source-tree archive retrieval failed: {result.stderr.decode('utf-8', 'replace').strip()}")


def cached_archive(url: str, commit_id: str) -> Path:
    parsed = urlsplit(url)
    slug = safe_component(f"{parsed.netloc}-{parsed.path}-{commit_id}")
    cache = default_cache_root().parent / "official-source-archives" / f"{slug}.tar.gz"
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.is_file():
        try:
            with tarfile.open(cache, mode="r:gz"):
                return cache
        except (tarfile.TarError, OSError):
            cache.unlink()
    stage = cache.with_name(f".{cache.name}.stage-{os.getpid()}")
    try:
        download_archive(url, stage)
        with tarfile.open(stage, mode="r:gz"):
            pass
        os.replace(stage, cache)
    finally:
        if stage.exists():
            stage.unlink()
    return cache


def find_registered_receipt_in_archive(
    archive: Path,
    *,
    expected_path: str,
    expected_bytes: int,
    expected_sha256: str,
) -> tuple[bytes, str]:
    matches: list[tuple[bytes, str]] = []
    try:
        with tarfile.open(archive, mode="r:gz") as handle:
            for member in handle:
                parts = Path(member.name).parts
                if not member.isfile() or len(parts) < 2 or member.size != expected_bytes:
                    continue
                relative = Path(*parts[1:]).as_posix()
                source = handle.extractfile(member)
                if source is None:
                    continue
                data = source.read()
                if sha256_bytes(data) != expected_sha256:
                    continue
                matches.append((data, relative))
    except (tarfile.TarError, OSError) as exc:
        raise CacheError("cannot inspect pinned archive for a registered receipt") from exc
    if len(matches) != 1:
        raise CacheError(
            "pinned archive did not contain exactly one registered receipt match "
            f"for {expected_path}: found {len(matches)}"
        )
    return matches[0]


def recover_registered_github_blob(record: SourceRecord) -> tuple[bytes, str] | None:
    specification = pinned_github_file_spec(record.locator)
    if specification is None:
        return None
    repository_url, commit_id, expected_path = specification
    exact_archive = archive_url(repository_url, commit_id)
    if exact_archive is None:
        return None
    archive = cached_archive(exact_archive, commit_id)
    data, resolved_path = find_registered_receipt_in_archive(
        archive,
        expected_path=expected_path,
        expected_bytes=record.raw_bytes,
        expected_sha256=record.raw_sha256,
    )
    return data, f"{repository_url}/blob/{commit_id}/{resolved_path}"


def read_exact_path_from_archive(archive: Path, expected_path: str) -> bytes | None:
    normalized = Path(expected_path).as_posix().lstrip("/")
    try:
        with tarfile.open(archive, mode="r:gz") as handle:
            matches = []
            for member in handle:
                parts = Path(member.name).parts
                if not member.isfile() or len(parts) < 2:
                    continue
                relative = Path(*parts[1:]).as_posix()
                if relative != normalized:
                    continue
                if member.size > MAX_DOWNLOAD_BYTES:
                    raise CacheError(f"pinned official source exceeds local limit: {expected_path}")
                source = handle.extractfile(member)
                if source is not None:
                    matches.append(source.read())
    except (tarfile.TarError, OSError) as exc:
        raise CacheError("cannot inspect pinned archive path") from exc
    if len(matches) > 1:
        raise CacheError(f"pinned archive path is ambiguous: {expected_path}")
    return matches[0] if matches else None


def recover_pinned_github_path(record: SourceRecord) -> tuple[bytes, str] | None:
    specification = pinned_github_file_spec(record.locator)
    if specification is None:
        return None
    repository_url, commit_id, expected_path = specification
    exact_archive = archive_url(repository_url, commit_id)
    if exact_archive is None:
        return None
    archive = cached_archive(exact_archive, commit_id)
    data = read_exact_path_from_archive(archive, expected_path)
    if data is None:
        return None
    return data, f"{repository_url}/blob/{commit_id}/{expected_path}"


def recover_registered_receipt_from_repositories(
    record: SourceRecord,
    repositories: tuple[tuple[str, str], ...],
) -> tuple[bytes, str] | None:
    matches: list[tuple[bytes, str]] = []
    for repository_url, commit_id in sorted(set(repositories)):
        exact_archive = archive_url(repository_url, commit_id)
        if exact_archive is None:
            continue
        archive = cached_archive(exact_archive, commit_id)
        try:
            data, resolved_path = find_registered_receipt_in_archive(
                archive,
                expected_path=Path(unquote(urlsplit(record.locator).path)).name,
                expected_bytes=record.raw_bytes,
                expected_sha256=record.raw_sha256,
            )
        except CacheError:
            continue
        matches.append(
            (data, f"{repository_url.rstrip('/')}/blob/{commit_id}/{resolved_path}")
        )
    if not matches:
        return None
    unique = {(sha256_bytes(data), locator): (data, locator) for data, locator in matches}
    if len(unique) != 1:
        raise CacheError(
            f"registered receipt matched multiple authority repositories: "
            f"{record.skill_id}/{record.source_id}"
        )
    return next(iter(unique.values()))


def archive_sources(archive: Path, selected: list[dict[str, Any]]) -> dict[str, bytes]:
    wanted = {item["path"] for item in selected}
    found: dict[str, bytes] = {}
    try:
        with tarfile.open(archive, mode="r:gz") as handle:
            for member in handle:
                parts = Path(member.name).parts
                if not member.isfile() or len(parts) < 2:
                    continue
                relative = Path(*parts[1:]).as_posix()
                if relative not in wanted:
                    continue
                source = handle.extractfile(member)
                if source is None:
                    raise CacheError(f"cannot read archived manual source: {relative}")
                found[relative] = source.read()
    except (tarfile.TarError, OSError) as exc:
        raise CacheError("cannot read exact source-tree archive") from exc
    missing = wanted - set(found)
    if missing:
        raise CacheError(f"source-tree archive is missing {len(missing)} inventoried manual files")
    return found


def materialize_inventory(
    root: Path,
    target: Path,
    record: SourceRecord,
    inventory: dict[str, Any],
    html2md: str,
) -> list[dict[str, Any]]:
    repository_url = inventory.get("repository_url")
    commit_id = inventory.get("commit_id")
    entries = inventory.get("entries")
    documentation_roots = inventory.get("documentation_roots")
    if (
        not isinstance(repository_url, str)
        or not isinstance(commit_id, str)
        or re.fullmatch(r"[a-f0-9]{40}", commit_id) is None
        or not isinstance(entries, list)
        or not isinstance(documentation_roots, list)
    ):
        raise CacheError(f"invalid source-tree inventory: {record.skill_id}/{record.authority_id}")
    source_url = urlsplit(record.locator)
    repo_url = urlsplit(repository_url)
    if (
        source_url.scheme != "https"
        or repo_url.scheme != "https"
        or source_url.netloc != repo_url.netloc
        or not source_url.path.startswith(repo_url.path.rstrip("/") + "/")
    ):
        raise CacheError(f"inventory repository does not match authority locator: {repository_url}")
    roots = [
        item.get("path")
        for item in documentation_roots
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    ]
    if not roots:
        raise CacheError(f"inventory has no documentation roots: {record.authority_id}")
    selected = [
        item
        for item in entries
        if isinstance(item, dict)
        and item.get("mode") == "100644"
        and item.get("object_type") == "blob"
        and isinstance(item.get("path"), str)
        and isinstance(item.get("object_id"), str)
        and manual_tree_entry(item["path"])
    ]
    if not selected:
        raise CacheError(f"inventory has no readable manual sources: {record.authority_id}")
    receipt_bytes = "".join(
        f"{item['mode']} {item['object_type']} {item['object_id']}\t{item['path']}\n"
        for item in sorted(entries, key=lambda value: value["path"])
    ).encode("utf-8")
    if len(receipt_bytes) != record.raw_bytes or sha256_bytes(receipt_bytes) != record.raw_sha256:
        raise CacheError(f"source-tree inventory receipt mismatch: {record.authority_id}")
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="official-manual-tree-") as temporary:
        temporary_path = Path(temporary)
        exact_archive = archive_url(repository_url, commit_id)
        archived: dict[str, bytes] | None = None
        checkout: Path | None = None
        if exact_archive is not None:
            archive = cached_archive(exact_archive, commit_id)
            archived = archive_sources(archive, selected)
        else:
            checkout = temporary_path / "checkout"
            checkout.mkdir()
            git_run(["init", "-q"], checkout)
            git_run(["remote", "add", "origin", repository_url], checkout)
            git_fetch_commit(repository_url, commit_id, checkout)
            git_run(["sparse-checkout", "init", "--cone"], checkout)
            git_run(["sparse-checkout", "set", *roots], checkout)
            git_run(["checkout", "-q", "--detach", "FETCH_HEAD"], checkout, timeout=600)
            actual_commit = git_run(["rev-parse", "HEAD"], checkout)
            if actual_commit != commit_id:
                raise CacheError(f"source-tree commit mismatch: {record.authority_id}")
        for item in selected:
            source_relative = Path(item["path"])
            if source_relative.is_absolute() or ".." in source_relative.parts:
                raise CacheError(f"unsafe inventoried source path: {source_relative}")
            if archived is not None:
                data = archived[source_relative.as_posix()]
            else:
                assert checkout is not None
                source = checkout / source_relative
                if not source.is_file() or source.is_symlink():
                    raise CacheError(f"missing inventoried manual source: {source_relative}")
                data = source.read_bytes()
            if git_blob_oid(data) != item["object_id"]:
                raise CacheError(f"git object mismatch: {source_relative}")
            derived_record = SourceRecord(
                skill_id=record.skill_id,
                authority_id=record.authority_id,
                source_id=f"{record.source_id}:{source_relative.as_posix()}",
                title=f"{record.title}: {source_relative.as_posix()}",
                source_kind="source-documentation",
                locator=(
                    f"{repository_url.rstrip('/')}/blob/{commit_id}/"
                    f"{source_relative.as_posix()}"
                ),
                retrieval_method="verified-git-object",
                raw_bytes=len(data),
                raw_sha256=sha256_bytes(data),
            )
            body, conversion = convert(derived_record, data, html2md, "")
            body, controls_changed = normalize_visible_controls(body)
            if controls_changed:
                conversion += "+visible-control-escapes"
            markdown = provenance_header(derived_record, conversion) + body
            output_relative = (
                Path(record.skill_id)
                / safe_component(record.authority_id)
                / "tree"
                / source_relative.parent
                / f"{source_relative.name}.md"
            )
            output = target / output_relative
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(markdown, encoding="utf-8", newline="\n")
            results.append(
                {
                    "authority_id": record.authority_id,
                    "conversion": conversion,
                    "git_blob_object_id": item["object_id"],
                    "markdown_bytes": output.stat().st_size,
                    "markdown_path": output_relative.as_posix(),
                    "markdown_sha256": sha256_file(output),
                    "official_source": derived_record.locator,
                    "raw_bytes": len(data),
                    "raw_sha256": sha256_bytes(data),
                    "skill_id": record.skill_id,
                    "source_id": derived_record.source_id,
                }
            )
    return results


def github_tree_spec(locator: str) -> tuple[str, str, str] | None:
    parsed = urlsplit(locator)
    parts = [part for part in parsed.path.split("/") if part]
    if (
        parsed.netloc != "github.com"
        or len(parts) < 5
        or parts[2] != "tree"
        or re.fullmatch(r"[a-f0-9]{40}", parts[3]) is None
    ):
        return None
    return (
        f"https://github.com/{parts[0]}/{parts[1]}",
        parts[3],
        "/".join(parts[4:]),
    )


def is_exact_repository_tree_record(record: SourceRecord) -> bool:
    return record.retrieval_method == "git-object" and github_tree_spec(record.locator) is not None


def materialize_unregistered_tree(
    target: Path,
    record: SourceRecord,
    repository_url: str,
    commit_id: str,
    tree_path: str,
    html2md: str,
) -> list[dict[str, Any]]:
    first = Path(tree_path).parts[0].lower()
    if first not in {"doc", "docs", "documentation", "examples"}:
        return []
    exact_archive = archive_url(repository_url, commit_id)
    if exact_archive is None:
        raise CacheError(f"unsupported exact tree transport: {record.locator}")
    archive = cached_archive(exact_archive, commit_id)
    sources: list[tuple[Path, bytes]] = []
    total_bytes = 0
    try:
        with tarfile.open(archive, mode="r:gz") as handle:
            for member in handle:
                parts = Path(member.name).parts
                if not member.isfile() or len(parts) < 2:
                    continue
                relative = Path(*parts[1:])
                relative_text = relative.as_posix()
                if not (
                    relative_text == tree_path
                    or relative_text.startswith(tree_path.rstrip("/") + "/")
                ):
                    continue
                if not manual_tree_entry(relative_text):
                    continue
                source = handle.extractfile(member)
                if source is None:
                    continue
                data = source.read()
                total_bytes += len(data)
                if total_bytes > 256 * 1024 * 1024 or len(sources) >= 4096:
                    raise CacheError(f"unregistered documentation tree exceeds local limits: {record.source_id}")
                sources.append((relative, data))
    except (tarfile.TarError, OSError) as exc:
        raise CacheError(f"cannot read exact documentation tree: {record.source_id}") from exc
    if not sources:
        raise CacheError(f"exact documentation tree contains no readable sources: {record.source_id}")
    results: list[dict[str, Any]] = []
    for source_relative, data in sources:
        derived_record = SourceRecord(
            skill_id=record.skill_id,
            authority_id=record.authority_id,
            source_id=f"{record.source_id}:{source_relative.as_posix()}",
            title=f"{record.title}: {source_relative.as_posix()}",
            source_kind="source-documentation",
            locator=(
                f"{repository_url.rstrip('/')}/blob/{commit_id}/"
                f"{source_relative.as_posix()}"
            ),
            retrieval_method="pinned-official-archive",
            raw_bytes=len(data),
            raw_sha256=sha256_bytes(data),
        )
        body, conversion = convert(derived_record, data, html2md, "")
        body, controls_changed = normalize_visible_controls(body)
        if controls_changed:
            conversion += "+visible-control-escapes"
        markdown = provenance_header(
            derived_record,
            conversion,
            receipt_status="pinned-archive-body-unregistered",
            actual_raw_bytes=len(data),
            actual_raw_sha256=sha256_bytes(data),
        ) + body
        output_relative = (
            Path(record.skill_id)
            / safe_component(record.authority_id)
            / "tree"
            / source_relative.parent
            / f"{source_relative.name}.md"
        )
        output = target / output_relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8", newline="\n")
        results.append(
            {
                "authority_id": record.authority_id,
                "conversion": conversion,
                "git_blob_object_id": git_blob_oid(data),
                "markdown_bytes": output.stat().st_size,
                "markdown_path": output_relative.as_posix(),
                "markdown_sha256": sha256_file(output),
                "official_source": derived_record.locator,
                "receipt_status": "pinned-archive-body-unregistered",
                "raw_bytes": len(data),
                "raw_sha256": sha256_bytes(data),
                "skill_id": record.skill_id,
                "source_id": derived_record.source_id,
            }
        )
    return results


def metadata_entry(
    target: Path,
    record: SourceRecord,
    *,
    conversion: str,
    explanation: str,
) -> dict[str, Any]:
    markdown = provenance_header(
        record,
        conversion,
        receipt_status=conversion,
        actual_raw_bytes=record.raw_bytes,
        actual_raw_sha256=record.raw_sha256,
    ) + explanation.rstrip() + "\n"
    relative = (
        Path(record.skill_id)
        / safe_component(record.authority_id)
        / f"{safe_component(record.source_id)}.md"
    )
    output = target / relative
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8", newline="\n")
    return {
        "authority_id": record.authority_id,
        "conversion": conversion,
        "markdown_bytes": output.stat().st_size,
        "markdown_path": relative.as_posix(),
        "markdown_sha256": sha256_file(output),
        "official_source": record.locator,
        "receipt_status": conversion,
        "skill_id": record.skill_id,
        "source_id": record.source_id,
    }


def build_cache(
    root: Path,
    target: Path,
    records: tuple[SourceRecord, ...],
    authorities: dict[str, Any],
    selected_skills: set[str],
    html2md: str,
    pdftotext: str,
    allow_live_drift: bool,
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    mirrored: set[tuple[str, str]] = set()
    inventoried: set[tuple[str, str]] = set()
    authority_repositories: dict[
        tuple[str, str],
        set[tuple[str, str]],
    ] = {}
    for candidate in records:
        file_spec = pinned_github_file_spec(candidate.locator)
        tree_spec = github_tree_spec(candidate.locator)
        specification = file_spec or tree_spec
        if specification is not None:
            repository_url, commit_id, _ = specification
            authority_repositories.setdefault(
                (candidate.skill_id, candidate.authority_id),
                set(),
            ).add((repository_url, commit_id))
    for record in records:
        if selected_skills and record.skill_id not in selected_skills:
            continue
        if not authority_allows(record, authorities):
            raise CacheError(f"source URL is outside authority policy: {record.locator}")
        mirror_key = (record.skill_id, record.authority_id)
        mirror = tracked_files(root, record.authority_id)
        if mirror and mirror_key not in mirrored:
            for source in mirror:
                relative = Path(record.skill_id) / safe_component(record.authority_id) / source.name
                output = target / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                snapshot = source.read_text(encoding="utf-8")
                snapshot, controls_changed = normalize_visible_controls(snapshot)
                snapshot_conversion = "validated-repository-snapshot"
                if controls_changed:
                    snapshot_conversion += "+visible-control-escapes"
                output.write_text(snapshot, encoding="utf-8", newline="\n")
                entries.append(
                    {
                        "authority_id": record.authority_id,
                        "conversion": snapshot_conversion,
                        "markdown_bytes": output.stat().st_size,
                        "markdown_path": relative.as_posix(),
                        "markdown_sha256": sha256_file(output),
                        "official_source": None,
                        "skill_id": record.skill_id,
                        "source_id": f"tracked:{source.name}",
                    }
                )
            mirrored.add(mirror_key)
        if mirror:
            continue
        authority = authorities[record.authority_id]
        if authority.get("provider_class") == "publisher":
            entries.append(
                metadata_entry(
                    target,
                    record,
                    conversion="external-publisher-body-not-retrieved",
                    explanation=(
                        "The registered authority supplies publication metadata or an "
                        "author-literature identity, not a redistributable software manual body. "
                        "Consult the official publisher URL under its access terms; do not treat "
                        "this cache record as a software parameter reference."
                    ),
                )
            )
            continue
        if record.retrieval_method == "git-object" and (
            record.source_kind not in BODY_SOURCE_KINDS
            or is_exact_repository_tree_record(record)
        ):
            inventory_key = (record.skill_id, record.authority_id)
            inventory = inventory_for(root, record.skill_id, record.authority_id)
            if inventory is not None and inventory_key not in inventoried:
                entries.extend(
                    materialize_inventory(root, target, record, inventory, html2md)
                )
                inventoried.add(inventory_key)
            if inventory is not None:
                continue
            tree = github_tree_spec(record.locator)
            if tree is not None:
                repository_url, commit_id, tree_path = tree
                materialized = materialize_unregistered_tree(
                    target,
                    record,
                    repository_url,
                    commit_id,
                    tree_path,
                    html2md,
                )
                if materialized:
                    entries.extend(materialized)
                else:
                    entries.append(
                        metadata_entry(
                            target,
                            record,
                            conversion="metadata-only-nonmanual-source-tree",
                            explanation=(
                                "This exact official tree is source or code inventory rather than "
                                "a documentation root. It is retained as provenance metadata and "
                                "is not presented as a parameter manual."
                            ),
                        )
                    )
                continue
        try:
            data, receipt_status, resolved_locator = fetch_bytes(
                record,
                allow_live_drift=allow_live_drift,
                fallback_repositories=tuple(
                    authority_repositories.get(
                        (record.skill_id, record.authority_id),
                        set(),
                    )
                ),
            )
        except CacheError:
            license_policy = authority.get("license_policy")
            if (
                isinstance(license_policy, dict)
                and license_policy.get("status") == "known-restricted"
            ):
                entries.append(
                    metadata_entry(
                        target,
                        record,
                        conversion="metadata-only-restricted-body-unavailable",
                        explanation=(
                            "The official body could not be retrieved through the registered "
                            "HTTPS route, and this authority is explicitly license-restricted. "
                            "The cache does not bypass access controls or substitute a third-party "
                            "copy. Consult the official locator under its terms; this record is "
                            "not manual body text and cannot support parameter-level claims."
                        ),
                    )
                )
                continue
            if record.source_kind != "index":
                raise
            entries.append(
                metadata_entry(
                    target,
                    record,
                    conversion="metadata-only-index-body-unavailable",
                    explanation=(
                        "This registered source is an inventory or search index rather than "
                        "a manual page. Its body was unavailable at refresh time, so the "
                        "official locator and registered identity are retained without "
                        "presenting unverified index bytes as manual content."
                    ),
                )
            )
            continue
        body, conversion = convert(record, data, html2md, pdftotext)
        body, controls_changed = normalize_visible_controls(body)
        if controls_changed:
            conversion += "+visible-control-escapes"
        markdown = provenance_header(
            record,
            conversion,
            receipt_status=receipt_status,
            actual_raw_bytes=len(data),
            actual_raw_sha256=sha256_bytes(data),
            resolved_locator=resolved_locator,
        ) + body
        if "\ufffd" in markdown:
            raise CacheError(f"replacement character in output: {record.skill_id}/{record.source_id}")
        relative = (
            Path(record.skill_id)
            / safe_component(record.authority_id)
            / f"{safe_component(record.source_id)}.md"
        )
        output = target / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8", newline="\n")
        entries.append(
            {
                "authority_id": record.authority_id,
                "conversion": conversion,
                "markdown_bytes": output.stat().st_size,
                "markdown_path": relative.as_posix(),
                "markdown_sha256": sha256_file(output),
                "official_source": resolved_locator,
                "registered_source": record.locator,
                "receipt_status": receipt_status,
                "raw_bytes": record.raw_bytes,
                "raw_sha256": record.raw_sha256,
                "live_raw_bytes": len(data),
                "live_raw_sha256": sha256_bytes(data),
                "skill_id": record.skill_id,
                "source_id": record.source_id,
            }
        )
    if selected_skills:
        missing = selected_skills - {entry["skill_id"] for entry in entries}
        if missing:
            raise CacheError(f"selected Skills have no materialized sources: {sorted(missing)}")
    write_indexes(target, entries)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "cache_policy": "local-only-no-redistribution",
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "html2md_identity": html2md_identity(html2md),
        "entries": entries,
    }
    (target / "manifest.json").write_text(canonical_json(manifest), encoding="utf-8")
    return manifest


def write_indexes(target: Path, entries: list[dict[str, Any]]) -> None:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        grouped.setdefault(entry["skill_id"], []).append(entry)
    global_lines = ["# Local official-manual Markdown cache", ""]
    for skill_id in sorted(grouped):
        skill_entries = sorted(grouped[skill_id], key=lambda item: item["markdown_path"])
        lines = [f"# {skill_id} official manuals", ""]
        for entry in skill_entries:
            relative = Path(entry["markdown_path"])
            local = Path(*relative.parts[1:])
            source = entry.get("official_source")
            suffix = f" — <{source}>" if source else ""
            lines.append(f"- [{entry['source_id']}]({local.as_posix()}){suffix}")
        lines.append("")
        (target / skill_id / "index.md").write_text("\n".join(lines), encoding="utf-8")
        global_lines.append(
            f"- [{skill_id}]({skill_id}/index.md): {len(skill_entries)} Markdown documents"
        )
    global_lines.append("")
    (target / "index.md").write_text("\n".join(global_lines), encoding="utf-8")


def routing_document(skill_id: str, records: list[SourceRecord]) -> str:
    authorities = sorted({record.authority_id for record in records})
    authority_lines = "\n".join(f"- `{authority_id}`" for authority_id in authorities)
    return (
        "# Local official-manual Markdown cache\n\n"
        "Use the repository-wide cache tool before relying on an external official "
        "document body that is not already present in this Skill. The tool accepts only "
        "registered HTTPS authorities, verifies pinned byte receipts, converts HTML with "
        "the repository-pinned `helloworld-Co/html2md`, preserves non-HTML source text "
        "losslessly, and writes third-party bodies outside Git.\n\n"
        "From the repository root:\n\n"
        "```bash\n"
        f"python3 tools/sync_official_manual_cache.py --refresh --skill {skill_id}\n"
        "python3 tools/sync_official_manual_cache.py --check\n"
        "```\n\n"
        "If a mutable official page has changed since its registered receipt, "
        "`--allow-live-drift` may be used to create a readable local copy only. The "
        "result is labeled `blocked-for-version-sensitive-use-until-registry-refresh`; "
        "never cite it as a receipt-verified versioned source.\n\n"
        "Read the generated `index.md` under "
        "`${XDG_CACHE_HOME:-$HOME/.cache}/vibe-dft-skills/official-manuals/"
        f"{skill_id}/`. Keep the official URL, authority/version identity, and local "
        "conversion label in every claim. A cache pass proves document identity and "
        "readability only; it does not prove executable behavior, convergence, physical "
        "validity, or permission to redistribute the cached body.\n\n"
        f"This Skill has {len(records)} registered source records across these authorities:\n\n"
        f"{authority_lines}\n"
    )


def manage_routing_documents(
    root: Path,
    records: tuple[SourceRecord, ...],
    *,
    check: bool,
) -> None:
    grouped: dict[str, list[SourceRecord]] = {}
    for record in records:
        grouped.setdefault(record.skill_id, []).append(record)
    failures: list[str] = []
    for skill_id in sorted(grouped):
        path = root / "skills" / skill_id / "references" / "manual-cache-route.md"
        expected = routing_document(skill_id, grouped[skill_id])
        if check:
            try:
                actual = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                failures.append(f"missing routing document: {path.relative_to(root)}")
                continue
            if actual != expected:
                failures.append(f"stale routing document: {path.relative_to(root)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8", newline="\n")
    if failures:
        raise CacheError("; ".join(failures))


def html2md_identity(executable: str) -> dict[str, Any]:
    result = subprocess.run(
        [executable, "--identity"],
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise CacheError(f"html2md identity failed: {result.stderr.strip()}")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise CacheError("html2md emitted invalid identity JSON") from exc
    if (
        not isinstance(value, dict)
        or value.get("upstream_url") != "https://github.com/helloworld-Co/html2md"
        or value.get("git_commit") != "ca08965af93e6565806a79087868daa439565ffc"
    ):
        raise CacheError("html2md is not the repository-pinned installation")
    return value


def validate_cache(cache_root: Path) -> dict[str, Any]:
    manifest_path = cache_root / "manifest.json"
    manifest = load_json(manifest_path)
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise CacheError("unsupported cache manifest")
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        raise CacheError("cache manifest has no entries")
    for entry in entries:
        if not isinstance(entry, dict):
            raise CacheError("malformed cache entry")
        relative = entry.get("markdown_path")
        if not isinstance(relative, str):
            raise CacheError("cache entry path is missing")
        path = cache_root / relative
        try:
            path.relative_to(cache_root)
        except ValueError as exc:
            raise CacheError("cache entry escapes the cache root") from exc
        if (
            not path.is_file()
            or path.stat().st_size != entry.get("markdown_bytes")
            or sha256_file(path) != entry.get("markdown_sha256")
        ):
            raise CacheError(f"cache entry identity mismatch: {relative}")
        text = path.read_text(encoding="utf-8")
        if "\ufffd" in text:
            raise CacheError(f"replacement character in cache entry: {relative}")
        forbidden_controls = {
            ord(character)
            for character in text
            if unicodedata.category(character) == "Cc" and character not in "\n\r\t"
        }
        if forbidden_controls:
            rendered = ", ".join(f"U+{value:04X}" for value in sorted(forbidden_controls))
            raise CacheError(f"invisible control characters in cache entry {relative}: {rendered}")
    return manifest


def refresh_transactionally(
    root: Path,
    cache_root: Path,
    records: tuple[SourceRecord, ...],
    authorities: dict[str, Any],
    selected_skills: set[str],
    html2md: str,
    pdftotext: str,
    allow_live_drift: bool,
) -> dict[str, Any]:
    cache_root.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{cache_root.name}.stage-", dir=cache_root.parent))
    backup = cache_root.with_name(f".{cache_root.name}.previous")
    try:
        manifest = build_cache(
            root,
            stage,
            records,
            authorities,
            selected_skills,
            html2md,
            pdftotext,
            allow_live_drift,
        )
        validate_cache(stage)
        if backup.exists():
            shutil.rmtree(backup)
        if cache_root.exists():
            os.replace(cache_root, backup)
        os.replace(stage, cache_root)
        if backup.exists():
            shutil.rmtree(backup)
        return manifest
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        if not cache_root.exists() and backup.exists():
            os.replace(backup, cache_root)
        raise


def default_cache_root() -> Path:
    base = os.environ.get("XDG_CACHE_HOME")
    return Path(base).expanduser() / "vibe-dft-skills" / "official-manuals" if base else (
        Path.home() / ".cache" / "vibe-dft-skills" / "official-manuals"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--cache-root", type=Path, default=default_cache_root())
    parser.add_argument("--skill", action="append", default=[])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--inventory", action="store_true")
    mode.add_argument("--refresh", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write-routing-docs", action="store_true")
    mode.add_argument("--check-routing-docs", action="store_true")
    parser.add_argument("--html2md", default=shutil.which("html2md") or "")
    parser.add_argument("--pdftotext", default=shutil.which("pdftotext") or "")
    parser.add_argument(
        "--allow-live-drift",
        action="store_true",
        help="materialize changed live official bytes but block version-sensitive use",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    cache_root = args.cache_root.expanduser().resolve()
    try:
        records = discover_records(root)
        authorities_data = load_yaml_strict(
            root / "registry" / "official-source-authorities.yaml",
            "official-source-authorities.yaml",
        )
        authorities = authorities_data.get("authorities")
        if not isinstance(authorities, dict):
            raise CacheError("official authority registry has no authorities mapping")
        selected = set(args.skill)
        known_skills = {record.skill_id for record in records}
        if selected - known_skills:
            raise CacheError(f"unknown or unbound Skills: {sorted(selected - known_skills)}")
        if args.inventory:
            scoped = [record for record in records if not selected or record.skill_id in selected]
            summary = {
                "records": len(scoped),
                "skills": sorted({record.skill_id for record in scoped}),
                "authorities": sorted({record.authority_id for record in scoped}),
                "tracked_mirror_authorities": sorted(
                    {record.authority_id for record in scoped if tracked_files(root, record.authority_id)}
                ),
            }
            print(canonical_json(summary), end="")
            return 0
        if args.write_routing_docs or args.check_routing_docs:
            manage_routing_documents(root, records, check=args.check_routing_docs)
            print(
                canonical_json(
                    {
                        "documents": len({record.skill_id for record in records}),
                        "status": "ok",
                    }
                ),
                end="",
            )
            return 0
        if args.check:
            manifest = validate_cache(cache_root)
        else:
            if not args.html2md or not args.pdftotext:
                raise CacheError("html2md and pdftotext executables are required")
            html2md_identity(args.html2md)
            manifest = refresh_transactionally(
                root,
                cache_root,
                records,
                authorities,
                selected,
                args.html2md,
                args.pdftotext,
                args.allow_live_drift,
            )
        print(
            canonical_json(
                {
                    "cache_root": str(cache_root),
                    "documents": len(manifest["entries"]),
                    "skills": len({entry["skill_id"] for entry in manifest["entries"]}),
                    "status": "ok",
                }
            ),
            end="",
        )
        return 0
    except (CacheError, OSError, UnicodeError, subprocess.SubprocessError) as exc:
        print(f"OFFICIAL_MANUAL_CACHE_ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
