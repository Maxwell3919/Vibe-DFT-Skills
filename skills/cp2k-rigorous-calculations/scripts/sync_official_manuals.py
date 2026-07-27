#!/usr/bin/env python3
"""Build or verify a complete version-matched CP2K manual snapshot."""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import http.client
import json
import os
import posixpath
from pathlib import Path
import re
import shutil
import ssl
import subprocess
import tempfile
import threading
import time
from typing import Any, Callable, Iterable
import urllib.error
from urllib.parse import unquote, urldefrag, urljoin, urlsplit
import urllib.request


SKILL_ROOT = Path(__file__).resolve().parent.parent
REFERENCES = SKILL_ROOT / "references"
DEFAULT_REGISTRY = REFERENCES / "manual-cache-receipts" / "source-registry.json"
DEFAULT_CACHE_ROOT = (
    Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    / "vibe-dft-skills"
    / "official-provider-mirrors"
    / "cp2k-rigorous-calculations"
)
DEFAULT_SNAPSHOT = DEFAULT_CACHE_ROOT / "provider-snapshot"
DEFAULT_HTML2MD_ADAPTER = SKILL_ROOT / "scripts" / "html2md_adapter.js"
DEFAULT_HTML2MD_ROOT = Path(
    os.environ.get("HTML2MD_ROOT", Path.home() / ".local" / "share" / "html2md")
)
DEFAULT_RAW_CACHE = (
    Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    / "vibe-dft-skills"
    / "cp2k-official-manual-raw"
)
VERSION = re.compile(r"^[0-9]{1,4}\.[0-9]{1,2}$")
ALLOWED_HOST = "manual.cp2k.org"
MAX_PAGE_BYTES = 20 * 1024 * 1024
HTML2MD_UPSTREAM = "https://github.com/helloworld-Co/html2md"
HTML2MD_COMMIT = "ca08965af93e6565806a79087868daa439565ffc"
PRIVATE_HEADERLINK = "\uf0c1"
WORD_TOKEN = re.compile(r"\w+", flags=re.UNICODE)
_HTTP_LOCAL = threading.local()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manual_branch(version: str) -> str:
    value = version.strip().casefold()
    if value == "trunk":
        return "trunk"
    if not VERSION.fullmatch(value):
        raise ValueError("version must be an explicit CP2K release such as 2026.2, or trunk")
    return f"cp2k-{value.replace('.', '_')}-branch"


def source_path(record: dict[str, Any], version: str) -> str:
    override = record.get("path_since")
    if not isinstance(override, dict):
        return record["path"]
    if version.strip().casefold() == "trunk":
        return override["path"]
    current = tuple(int(part) for part in version.split("."))
    threshold = tuple(int(part) for part in override["version"].split("."))
    return override["path"] if current >= threshold else record["path"]


def verified_context() -> ssl.SSLContext:
    try:
        import certifi
    except ModuleNotFoundError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


def fetch(url: str, *, timeout: float = 30.0, attempts: int = 10) -> bytes:
    if urlsplit(url).hostname != ALLOWED_HOST or urlsplit(url).scheme != "https":
        raise ValueError("only HTTPS sources from manual.cp2k.org are allowed")
    request = urllib.request.Request(url, headers={"User-Agent": "vibe-dft-skills-cp2k-mirror/1.0"})
    context = verified_context()
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
                final_url = response.geturl()
                if urlsplit(final_url).hostname != ALLOWED_HOST or urlsplit(final_url).scheme != "https":
                    raise ValueError("official source redirected outside manual.cp2k.org")
                body = response.read(MAX_PAGE_BYTES + 1)
                if len(body) > MAX_PAGE_BYTES:
                    raise ValueError("official page exceeds the configured size limit")
                return body
        except urllib.error.HTTPError as exc:
            transient = exc.code in {408, 425, 429} or exc.code >= 500
            if not transient or attempt + 1 == attempts:
                raise
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, ssl.SSLCertVerificationError) or attempt + 1 == attempts:
                raise
        except (ConnectionError, TimeoutError, ssl.SSLError):
            if attempt + 1 == attempts:
                raise
        time.sleep(min(0.25 * (2**attempt), 8.0))
    raise RuntimeError("unreachable retry state")


def cache_fetched_body(url: str, body: bytes) -> None:
    """Persist a verified complete response so interrupted refreshes resume."""

    cache = DEFAULT_RAW_CACHE / f"{sha256_bytes(url.encode('utf-8'))}.html"
    cache.parent.mkdir(parents=True, exist_ok=True)
    temporary = cache.with_name(f".{cache.name}.stage-{os.getpid()}-{time.time_ns()}")
    temporary.write_bytes(body)
    os.replace(temporary, cache)


def fetch_persistent(url: str, *, attempts: int = 12) -> bytes:
    """Fetch with one reusable TLS connection per worker thread."""

    if urlsplit(url).hostname != ALLOWED_HOST or urlsplit(url).scheme != "https":
        raise ValueError("only HTTPS sources from manual.cp2k.org are allowed")
    cache = DEFAULT_RAW_CACHE / f"{sha256_bytes(url.encode('utf-8'))}.html"
    if cache.is_file():
        body = cache.read_bytes()
        if body and len(body) <= MAX_PAGE_BYTES:
            return body
    parsed = urlsplit(url)
    request_path = parsed.path + (f"?{parsed.query}" if parsed.query else "")
    last_error: Exception | None = None
    for attempt in range(attempts):
        connection = getattr(_HTTP_LOCAL, "connection", None)
        if connection is None:
            connection = http.client.HTTPSConnection(
                ALLOWED_HOST,
                timeout=45,
                context=verified_context(),
            )
            _HTTP_LOCAL.connection = connection
        try:
            connection.request(
                "GET",
                request_path,
                headers={
                    "User-Agent": "vibe-dft-skills-cp2k-mirror/1.0",
                    "Accept-Encoding": "identity",
                    "Connection": "keep-alive",
                },
            )
            response = connection.getresponse()
            body = response.read(MAX_PAGE_BYTES + 1)
            if response.status != 200:
                raise urllib.error.HTTPError(
                    url,
                    response.status,
                    response.reason,
                    response.headers,
                    None,
                )
            if len(body) > MAX_PAGE_BYTES:
                raise ValueError("official page exceeds the configured size limit")
            cache_fetched_body(url, body)
            return body
        except (OSError, http.client.HTTPException, ssl.SSLError, urllib.error.HTTPError) as exc:
            last_error = exc
            try:
                connection.close()
            finally:
                _HTTP_LOCAL.connection = None
            if isinstance(exc, urllib.error.HTTPError):
                transient = exc.code in {408, 425, 429} or exc.code >= 500
                if not transient:
                    raise
            if attempt + 1 < attempts:
                time.sleep(min(0.25 * (2**attempt), 8.0))
    raise RuntimeError(f"persistent official fetch failed: {url}: {last_error}")


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href)


def discover_index_pages(html: bytes, genindex_url: str) -> list[str]:
    parser = LinkParser()
    parser.feed(html.decode("utf-8", errors="replace"))
    branch_root = genindex_url.rsplit("/", 1)[0] + "/"
    pages: set[str] = set()
    for href in parser.links:
        absolute = urldefrag(urljoin(genindex_url, href))[0]
        parts = urlsplit(absolute)
        if (
            absolute.startswith(branch_root)
            and parts.hostname == ALLOWED_HOST
            and parts.path.endswith(".html")
            and "/_static/" not in parts.path
        ):
            pages.add(absolute.removeprefix(branch_root))
    if "CP2K_INPUT.html" not in pages or len(pages) < 100:
        raise ValueError("official genindex did not yield a credible CP2K manual inventory")
    return sorted(pages)


def html2md_identity(
    *,
    adapter_path: Path = DEFAULT_HTML2MD_ADAPTER,
    html2md_root: Path = DEFAULT_HTML2MD_ROOT,
) -> dict[str, Any]:
    if not adapter_path.is_file():
        raise RuntimeError(f"html2md adapter is missing: {adapter_path}")
    command = [
        "node",
        str(adapter_path),
        "--html2md-root",
        str(html2md_root),
        "--identity",
    ]
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"html2md identity check failed: {detail}")
    try:
        identity = json.loads(completed.stdout.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("html2md identity output is not valid UTF-8 JSON") from exc
    required = {
        "adapter_schema_version",
        "dependencies",
        "expected_upstream_commit",
        "git_commit",
        "project_name",
        "project_version",
        "upstream_url",
    }
    if not isinstance(identity, dict) or set(identity) != required:
        raise RuntimeError("html2md identity has an unsupported structure")
    if (
        identity["git_commit"] != HTML2MD_COMMIT
        or identity["expected_upstream_commit"] != HTML2MD_COMMIT
        or identity["upstream_url"] != HTML2MD_UPSTREAM
        or identity["project_name"] != "hello-html2md"
        or identity["adapter_schema_version"] != "1.0"
    ):
        raise RuntimeError("html2md identity does not match the pinned converter")
    dependencies = identity["dependencies"]
    if (
        not isinstance(dependencies, dict)
        or set(dependencies) != {"jsdom", "turndown", "turndown-plugin-gfm"}
        or not all(isinstance(value, str) and value for value in dependencies.values())
    ):
        raise RuntimeError("html2md dependency identity is incomplete")
    return identity


def run_html2md(
    html: str,
    *,
    adapter_path: Path = DEFAULT_HTML2MD_ADAPTER,
    html2md_root: Path = DEFAULT_HTML2MD_ROOT,
) -> str:
    completed = subprocess.run(
        [
            "node",
            str(adapter_path),
            "--html2md-root",
            str(html2md_root),
        ],
        input=html.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=120,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"html2md conversion failed: {detail}")
    try:
        markdown = completed.stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeError("html2md produced invalid UTF-8") from exc
    if not markdown.strip():
        raise RuntimeError("html2md produced empty Markdown")
    return markdown


def markdown_path_for(
    source_path_value: str,
    curated_paths: dict[str, str],
) -> str:
    """Map one official HTML path to a stable repository Markdown path."""

    if source_path_value in curated_paths:
        return f"{curated_paths[source_path_value]}.md"
    decoded = unquote(source_path_value)
    path = Path(decoded)
    if path.is_absolute() or ".." in path.parts or path.suffix.casefold() != ".html":
        raise ValueError(f"unsafe CP2K manual inventory path: {source_path_value}")
    return (Path("pages") / path.with_suffix(".md")).as_posix()


def cp2k_source_id(source_path_value: str) -> str:
    return f"cp2k-page-{sha256_bytes(source_path_value.encode('utf-8'))[:32]}"


def local_markdown_link_count(markdown: str) -> int:
    count = 0
    for href in re.findall(r"(?<!!)\[[^\]]*\]\(([^)\s]+)", markdown):
        href = href.strip("<>")
        if not urlsplit(href).scheme and not href.startswith("//"):
            count += 1
    return count


def rewrite_internal_href(
    href: str,
    *,
    source_url: str,
    source_output_path: str,
    branch_root: str,
    output_paths: dict[str, str],
) -> tuple[str, dict[str, str] | None]:
    """Rewrite one same-version manual link and return its closure receipt."""

    absolute = urljoin(source_url, href)
    target_url, fragment = urldefrag(absolute)
    if not target_url:
        target_url = urldefrag(source_url)[0]
    parts = urlsplit(target_url)
    if (
        parts.scheme != "https"
        or parts.hostname != ALLOWED_HOST
        or not target_url.startswith(branch_root)
        or not parts.path.endswith(".html")
    ):
        return absolute, None
    target_source_path = unquote(target_url.removeprefix(branch_root))
    target_output_path = output_paths.get(target_source_path)
    if target_output_path is None:
        raise ValueError(
            "same-version CP2K manual link is outside the official index: "
            f"{target_source_path}"
        )
    if target_output_path == source_output_path:
        local = ""
    else:
        start = posixpath.dirname(source_output_path) or "."
        local = posixpath.relpath(target_output_path, start=start)
    local_href = local + (f"#{fragment}" if fragment else "")
    if not local_href:
        local_href = Path(target_output_path).name
    return local_href, {
        "target_source_path": target_source_path,
        "target_markdown_path": target_output_path,
        "fragment": fragment,
        "local_href": local_href,
    }


def discover_page_links(
    source_url: str,
    body: bytes,
    *,
    branch_root: str,
) -> set[str]:
    """Return every same-version HTML target in one official manual page."""

    try:
        from bs4 import BeautifulSoup
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "beautifulsoup4 is required to discover the CP2K manual link closure"
        ) from exc
    source = body.decode("utf-8", errors="strict")
    soup = BeautifulSoup(source, "lxml")
    targets: set[str] = set()
    for node in soup.find_all(href=True):
        href = node.get("href")
        if not isinstance(href, str) or not href:
            continue
        target_url = urldefrag(urljoin(source_url, href))[0]
        parts = urlsplit(target_url)
        if (
            parts.scheme != "https"
            or parts.hostname != ALLOWED_HOST
            or not target_url.startswith(branch_root)
            or not parts.path.endswith(".html")
        ):
            continue
        target = unquote(target_url.removeprefix(branch_root))
        path = Path(target)
        if path.is_absolute() or ".." in path.parts or path.suffix.casefold() != ".html":
            raise ValueError(f"unsafe linked CP2K manual path: {target}")
        targets.add(target)
    return targets


def discover_link_closure(
    seed_pages: list[str],
    *,
    branch_root: str,
    workers: int,
) -> tuple[list[str], int]:
    """Recursively fetch the full same-version HTML link closure."""

    discovered = set(seed_pages)
    frontier = set(seed_pages)
    while frontier:
        next_frontier: set[str] = set()
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    fetch_persistent,
                    branch_root + source_path_value,
                ): source_path_value
                for source_path_value in sorted(frontier)
            }
            for future in as_completed(futures):
                source_path_value = futures[future]
                try:
                    body = future.result()
                    targets = discover_page_links(
                        branch_root + source_path_value,
                        body,
                        branch_root=branch_root,
                    )
                except Exception as exc:
                    raise RuntimeError(
                        "official link-closure discovery failed: "
                        f"{source_path_value} ({type(exc).__name__}: {exc})"
                    ) from exc
                next_frontier.update(targets - discovered)
        discovered.update(next_frontier)
        frontier = next_frontier
        if len(discovered) > 20_000:
            raise ValueError("CP2K manual link closure exceeds the safety limit")
    return sorted(discovered), len(discovered) - len(seed_pages)


def prepare_article_with_links(
    url: str,
    body: bytes,
    topic: str,
    *,
    output_path: str,
    branch_root: str,
    output_paths: dict[str, str],
) -> tuple[str, str, list[dict[str, str]], list[str]]:
    try:
        from bs4 import BeautifulSoup
    except ModuleNotFoundError as exc:
        raise RuntimeError("beautifulsoup4 is required to refresh the CP2K manual snapshot") from exc
    try:
        source = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(f"official page is not valid UTF-8: {topic}") from exc
    if "\ufffd" in source:
        raise ValueError(f"official page contains a replacement character: {topic}")
    soup = BeautifulSoup(source, "lxml")
    article = soup.find("article") or soup.find("main") or soup.find(attrs={"role": "main"})
    if article is None:
        raise ValueError(f"official page has no supported main-content element: {topic}")
    for node in article.find_all(["script", "style", "nav", "form"]):
        node.decompose()
    for node in article.select("a.headerlink"):
        node.decompose()
    for node in article.select("[aria-hidden='true']"):
        node.decompose()
    anchors: list[str] = []
    seen_anchors: set[str] = set()
    for node in list(article.find_all(attrs={"id": True})):
        anchor_id = node.get("id")
        if not isinstance(anchor_id, str) or not anchor_id or anchor_id in seen_anchors:
            continue
        anchor = soup.new_tag("a")
        anchor["id"] = anchor_id
        anchor["data-cp2k-manual-anchor"] = "true"
        node.insert_before(anchor)
        anchors.append(anchor_id)
        seen_anchors.add(anchor_id)
    # Sphinx's general index uses headerless tables only for multi-column
    # layout. Turndown correctly keeps such tables as raw HTML, but that creates
    # megabyte-long Markdown lines. Unwrap only this presentation table and
    # retain its nested semantic lists.
    for table in article.select("table.indextable"):
        for wrapper in table.find_all(
            ["tbody", "thead", "tfoot", "tr", "td", "th"]
        ):
            wrapper.unwrap()
        table.unwrap()
    # Sphinx wraps otherwise inline GFM table-cell content in ``<p>`` nodes.
    # Turndown preserves the paragraph's blank lines, which splits one logical
    # table row across several Markdown lines and prevents GitHub from
    # rendering it as a table. Unwrap only direct cell paragraphs; keep their
    # links, emphasis, code, and exact text intact.
    for table in article.find_all("table"):
        for paragraph in table.select("th > p, td > p"):
            paragraph.unwrap()
    internal_links: list[dict[str, str]] = []
    for node in article.find_all(True):
        value = node.get("href")
        if isinstance(value, str) and value:
            rewritten, receipt = rewrite_internal_href(
                value,
                source_url=url,
                source_output_path=output_path,
                branch_root=branch_root,
                output_paths=output_paths,
            )
            node["href"] = rewritten
            if receipt is not None:
                internal_links.append(receipt)
        value = node.get("src")
        if isinstance(value, str) and value:
            node["src"] = urljoin(url, value)
        if node.name == "img":
            for attribute in ("data-src", "data-original-src", "data-original"):
                value = node.get(attribute)
                if isinstance(value, str) and value:
                    node["src"] = urljoin(url, value)
                    break
    # Preserve adjacency between syntax-highlighted inline spans. Supplying a
    # separator here would turn source tokens such as ``300K`` into artificial
    # ``300``/``K`` pairs and make the loss detector report false damage.
    source_text = article.get_text()
    if len(WORD_TOKEN.findall(source_text)) < 3:
        raise ValueError(f"official page extraction is unexpectedly empty: {topic}")
    return str(article), source_text, internal_links, anchors


def prepare_article(url: str, body: bytes, topic: str) -> tuple[str, str]:
    """Compatibility wrapper used by focused extraction tests."""

    source_path_value = unquote(urlsplit(url).path.rsplit("/", 1)[-1])
    branch_root = "https://manual.cp2k.org/__compatibility_no_rewrite__/"
    output_path = Path(source_path_value).with_suffix(".md").as_posix()
    html, source_text, _links, _anchors = prepare_article_with_links(
        url,
        body,
        topic,
        output_path=output_path,
        branch_root=branch_root,
        output_paths={source_path_value: output_path},
    )
    return html, source_text


def markdown_word_tokens(markdown: str) -> list[str]:
    # Remove Turndown emphasis markers before unescaping literal Markdown
    # punctuation. This reconstructs adjacent source text such as
    # ``alpha<em>g</em>`` without erasing an official escaped ``\*``.
    lines: list[str] = []
    active_fence: int | None = None
    for line in markdown.splitlines(keepends=True):
        fence = re.match(r"^(`{3,})(.*)$", line)
        if active_fence is None and fence:
            active_fence = len(fence.group(1))
            lines.append(line)
            continue
        if (
            active_fence is not None
            and fence
            and len(fence.group(1)) >= active_fence
            and not fence.group(2).strip()
        ):
            active_fence = None
            lines.append(line)
            continue
        if active_fence is None:
            line = re.sub(
                r"</?(?:sub|sup)>",
                "",
                line,
                flags=re.IGNORECASE,
            )
        lines.append(line)
    markdown_without_html_typography = "".join(lines)
    markdown_without_emphasis = re.sub(
        r"(?<!\\)\*",
        "",
        markdown_without_html_typography,
    )
    markdown_unescaped = re.sub(
        r"\\([\\`*_{}\[\]()#+\-.!<>])",
        r"\1",
        markdown_without_emphasis,
    )
    return WORD_TOKEN.findall(markdown_unescaped)


def token_sequence_preserved(source_text: str, markdown: str) -> bool:
    source_characters = (
        character.casefold()
        for character in source_text
        if character.isalnum()
    )
    markdown_characters = iter(
        character.casefold()
        for character in markdown
        if character.isalnum()
    )
    for source_character in source_characters:
        for markdown_character in markdown_characters:
            if markdown_character == source_character:
                break
        else:
            return False
    return True


def conversion_quality(source_text: str, markdown: str, topic: str) -> dict[str, Any]:
    if "\ufffd" in markdown:
        raise ValueError(f"Markdown contains a replacement character: {topic}")
    if PRIVATE_HEADERLINK in markdown:
        raise ValueError(f"Markdown contains the Sphinx private-use header glyph: {topic}")
    source_tokens = WORD_TOKEN.findall(source_text)
    markdown_tokens = markdown_word_tokens(markdown)
    if not token_sequence_preserved(source_text, markdown):
        raise ValueError(f"Markdown lost or reordered official text tokens: {topic}")
    source_non_ascii = Counter(
        character
        for character in source_text
        if ord(character) > 127 and not character.isspace()
    )
    markdown_non_ascii = Counter(
        character
        for character in markdown
        if ord(character) > 127 and not character.isspace()
    )
    missing_non_ascii = {
        character: count - markdown_non_ascii[character]
        for character, count in source_non_ascii.items()
        if markdown_non_ascii[character] < count
    }
    if missing_non_ascii:
        rendered = ", ".join(
            f"U+{ord(character):04X}:{count}"
            for character, count in sorted(missing_non_ascii.items())
        )
        raise ValueError(f"Markdown lost non-ASCII characters for {topic}: {rendered}")
    if len(markdown_tokens) < len(source_tokens):
        raise ValueError(f"Markdown token count is smaller than source text: {topic}")
    max_line_chars = max((len(line) for line in markdown.splitlines()), default=0)
    if max_line_chars > 20_000:
        raise ValueError(f"Markdown contains an unreadably long line: {topic}")
    return {
        "status": "pass",
        "source_text_sha256": sha256_bytes(source_text.encode("utf-8")),
        "source_text_chars": len(source_text),
        "source_token_count": len(source_tokens),
        "source_alphanumeric_character_count": sum(
            character.isalnum() for character in source_text
        ),
        "source_non_ascii_chars": sum(source_non_ascii.values()),
        "markdown_token_count": len(markdown_tokens),
        "max_line_chars": max_line_chars,
        "token_sequence_preserved": True,
        "non_ascii_characters_preserved": True,
        "replacement_characters": 0,
        "sphinx_private_header_glyphs": 0,
    }


def render_page(
    topic: str,
    url: str,
    body: bytes,
    *,
    output_path: str,
    branch_root: str,
    output_paths: dict[str, str],
    converter: Callable[[str], str],
    converter_identity: dict[str, Any],
) -> tuple[bytes, dict[str, Any]]:
    article_html, source_text, internal_links, anchors = prepare_article_with_links(
        url,
        body,
        topic,
        output_path=output_path,
        branch_root=branch_root,
        output_paths=output_paths,
    )
    converted = converter(article_html)
    text = (
        f"# CP2K official manual snapshot: {topic}\n\n"
        f"- Source: {url}\n"
        f"- Raw SHA-256: {sha256_bytes(body)}\n"
        f"- Converter: helloworld-Co/html2md at "
        f"`{converter_identity['git_commit']}`; adapter schema "
        f"`{converter_identity['adapter_schema_version']}`.\n"
        "- Status: version-matched cached official text; reopen the source for current live verification.\n\n"
        "---\n\n"
        + converted.strip()
        + "\n"
    )
    quality = conversion_quality(source_text, text, topic)
    quality["internal_links"] = internal_links
    quality["anchors"] = anchors
    return text.encode("utf-8"), quality


def page_to_markdown(
    topic: str,
    url: str,
    body: bytes,
    *,
    converter: Callable[[str], str] | None = None,
    converter_identity: dict[str, Any] | None = None,
    output_path: str = "page.md",
    branch_root: str | None = None,
    output_paths: dict[str, str] | None = None,
) -> bytes:
    identity = converter_identity or html2md_identity()
    active_converter = converter or run_html2md
    rendered, _quality = render_page(
        topic,
        url,
        body,
        output_path=output_path,
        branch_root=branch_root or url.rsplit("/", 1)[0] + "/",
        output_paths=output_paths or {url.rsplit("/", 1)[-1]: output_path},
        converter=active_converter,
        converter_identity=identity,
    )
    return rendered


def load_registry(path: Path) -> dict[str, Any]:
    registry = json.loads(path.read_text(encoding="utf-8"))
    if registry.get("schema_version") != "1.0" or not isinstance(registry.get("topics"), dict):
        raise ValueError("official-source registry has an unsupported structure")
    for topic, record in registry["topics"].items():
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", topic):
            raise ValueError(f"invalid topic identifier: {topic}")
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise ValueError(f"invalid source-registry record: {topic}")
    return registry


def _fetch_topic(item: tuple[str, str]) -> tuple[str, str, bytes]:
    topic, url = item
    return topic, url, fetch_persistent(url)


def _fetch_and_render(
    item: tuple[str, str],
    *,
    output_path: str,
    branch_root: str,
    output_paths: dict[str, str],
    converter_identity: dict[str, Any],
    adapter_path: Path,
    html2md_root: Path,
) -> tuple[str, str, bytes, bytes, dict[str, Any]]:
    topic, url, body = _fetch_topic(item)
    rendered, quality = render_page(
        topic,
        url,
        body,
        output_path=output_path,
        branch_root=branch_root,
        output_paths=output_paths,
        converter=lambda html: run_html2md(
            html,
            adapter_path=adapter_path,
            html2md_root=html2md_root,
        ),
        converter_identity=converter_identity,
    )
    return topic, url, body, rendered, quality


def refresh_snapshot(
    version: str,
    *,
    registry_path: Path = DEFAULT_REGISTRY,
    snapshot_dir: Path = DEFAULT_SNAPSHOT,
    workers: int = 4,
    adapter_path: Path = DEFAULT_HTML2MD_ADAPTER,
    html2md_root: Path = DEFAULT_HTML2MD_ROOT,
) -> dict[str, Any]:
    if workers < 1 or workers > 16:
        raise ValueError("workers must be between 1 and 16")
    registry = load_registry(registry_path)
    branch = manual_branch(version)
    root = registry["manual_root"].rstrip("/") + f"/{branch}/"
    genindex_url = root + "genindex.html"
    genindex = fetch(genindex_url, timeout=60.0)
    index_inventory = discover_index_pages(genindex, genindex_url)
    inventory, linked_page_count = discover_link_closure(
        index_inventory,
        branch_root=root,
        workers=workers,
    )
    curated_source_topics = {
        source_path(record, version): topic
        for topic, record in registry["topics"].items()
    }
    missing_curated = set(curated_source_topics) - set(inventory)
    if missing_curated:
        raise ValueError(
            "registered CP2K topics are absent from the official index: "
            + ", ".join(sorted(missing_curated))
        )
    output_paths = {
        page: markdown_path_for(page, curated_source_topics)
        for page in inventory
    }
    if len(set(output_paths.values())) != len(output_paths):
        raise ValueError("CP2K manual path mapping is not one-to-one")
    page_urls = {page: root + page for page in inventory}
    converter_identity = html2md_identity(
        adapter_path=adapter_path,
        html2md_root=html2md_root,
    )
    retrieved = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    with tempfile.TemporaryDirectory(prefix="cp2k-manual-stage-", dir=REFERENCES) as temporary:
        stage = Path(temporary) / "official-manual"
        stage.mkdir()
        page_records: dict[str, Any] = {}
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    _fetch_and_render,
                    item,
                    output_path=output_paths[item[0]],
                    branch_root=root,
                    output_paths=output_paths,
                    converter_identity=converter_identity,
                    adapter_path=adapter_path,
                    html2md_root=html2md_root,
                ): item[0]
                for item in page_urls.items()
            }
            for future in as_completed(futures):
                try:
                    topic, url, body, rendered, quality = future.result()
                except Exception as exc:
                    raise RuntimeError(
                        f"official topic fetch failed: {futures[future]} ({type(exc).__name__})"
                    ) from exc
                filename = output_paths[topic]
                output = stage / filename
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(rendered)
                source_id = cp2k_source_id(topic)
                if source_id in page_records:
                    raise ValueError(f"colliding CP2K source identifier: {source_id}")
                page_records[source_id] = {
                    "path": filename,
                    "source_url": url,
                    "source_path": topic,
                    "curated_topic": curated_source_topics.get(topic),
                    "raw_sha256": sha256_bytes(body),
                    "raw_bytes": len(body),
                    "snapshot_sha256": sha256_bytes(rendered),
                    "snapshot_bytes": len(rendered),
                    "indexed": True,
                    "conversion_quality": quality,
                }
        records_by_source = {
            record["source_path"]: record
            for record in page_records.values()
        }
        anchors_by_source = {
            record["source_path"]: set(record["conversion_quality"]["anchors"])
            for record in page_records.values()
        }
        internal_link_count = 0
        for source_id, record in page_records.items():
            quality = record["conversion_quality"]
            anchors = quality.pop("anchors")
            links = quality.pop("internal_links")
            for link in links:
                target = records_by_source.get(link["target_source_path"])
                if target is None:
                    raise ValueError(
                        f"unresolved CP2K internal link in {source_id}: "
                        f"{link['target_source_path']}"
                    )
                fragment = link["fragment"]
                if fragment and fragment not in anchors_by_source[link["target_source_path"]]:
                    raise ValueError(
                        f"unresolved CP2K internal anchor in {source_id}: "
                        f"{link['target_source_path']}#{fragment}"
                    )
            quality["anchor_count"] = len(anchors)
            markdown = (stage / record["path"]).read_text(encoding="utf-8")
            quality["internal_link_count"] = local_markdown_link_count(markdown)
            internal_link_count += quality["internal_link_count"]
        inventory_record = {
            "schema_version": "2.0",
            "manual_version": version,
            "manual_branch": branch,
            "source_url": genindex_url,
            "source_sha256": sha256_bytes(genindex),
            "genindex_page_count": len(index_inventory),
            "linked_page_count": linked_page_count,
            "page_count": len(inventory),
            "pages": inventory,
        }
        inventory_bytes = (json.dumps(inventory_record, indent=2, sort_keys=True) + "\n").encode("utf-8")
        (stage / "index.json").write_bytes(inventory_bytes)
        manual_index_lines = [
            "# CP2K 2026.2 complete official manual mirror",
            "",
            f"- Official index: <{genindex_url}>",
            f"- Mirrored pages: {len(page_records)}",
            f"- General-index pages: {len(index_inventory)}",
            f"- Additional recursively linked pages: {linked_page_count}",
            "- Coverage gate: the official general index and its complete same-version HTML link closure are present.",
            "- Link gate: every same-version manual link and fragment is checked locally.",
            "",
            "## Pages",
            "",
        ]
        for _source_id, record in sorted(page_records.items()):
            label = record.get("curated_topic") or record["source_path"]
            manual_index_lines.append(f"- [{label}]({record['path']})")
        manual_index_bytes = (
            "\n".join(manual_index_lines).rstrip() + "\n"
        ).encode("utf-8")
        (stage / "manual-index.md").write_bytes(manual_index_bytes)
        manifest = {
            "schema_version": "2.0",
            "manual_version": version,
            "manual_branch": branch,
            "retrieved_utc": retrieved,
            "converter": {
                **converter_identity,
                "adapter_path": "scripts/html2md_adapter.js",
                "adapter_sha256": sha256_file(adapter_path),
            },
            "registry_sha256": sha256_file(registry_path),
            "index_sha256": sha256_bytes(inventory_bytes),
            "manual_index_sha256": sha256_bytes(manual_index_bytes),
            "index_page_count": len(inventory),
            "genindex_page_count": len(index_inventory),
            "linked_page_count": linked_page_count,
            "mirrored_page_count": len(page_records),
            "mirrored_topic_count": len(page_records),
            "curated_topic_count": len(curated_source_topics),
            "internal_link_count": internal_link_count,
            "pages": dict(sorted(page_records.items())),
        }
        (stage / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        backup = snapshot_dir.with_name(snapshot_dir.name + ".backup")
        if backup.exists():
            shutil.rmtree(backup)
        if snapshot_dir.exists():
            snapshot_dir.replace(backup)
        try:
            stage.replace(snapshot_dir)
        except Exception:
            if backup.exists() and not snapshot_dir.exists():
                backup.replace(snapshot_dir)
            raise
        finally:
            if backup.exists():
                shutil.rmtree(backup)
    return manifest


def check_snapshot(
    *,
    registry_path: Path = DEFAULT_REGISTRY,
    snapshot_dir: Path = DEFAULT_SNAPSHOT,
) -> dict[str, Any]:
    registry = load_registry(registry_path)
    manifest_path = snapshot_dir / "manifest.json"
    index_path = snapshot_dir / "index.json"
    manual_index_path = snapshot_dir / "manual-index.md"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    index = json.loads(index_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if manifest.get("schema_version") != "2.0" or index.get("schema_version") != "2.0":
        errors.append("snapshot schema version is unsupported")
    if manifest.get("manual_version") != index.get("manual_version"):
        errors.append("manifest and index versions differ")
    if manifest.get("manual_branch") != index.get("manual_branch"):
        errors.append("manifest and index branches differ")
    if manifest.get("registry_sha256") != sha256_file(registry_path):
        errors.append("official-source registry changed after snapshot generation")
    if manifest.get("index_sha256") != sha256_file(index_path):
        errors.append("official manual index hash mismatch")
    if (
        not manual_index_path.is_file()
        or manifest.get("manual_index_sha256") != sha256_file(manual_index_path)
    ):
        errors.append("human-readable manual index hash mismatch")
    if index.get("page_count") != len(index.get("pages", [])) or index.get("page_count", 0) < 100:
        errors.append("official manual index is incomplete")
    if (
        not isinstance(index.get("genindex_page_count"), int)
        or not isinstance(index.get("linked_page_count"), int)
        or index.get("genindex_page_count", 0) + index.get("linked_page_count", 0)
        != index.get("page_count")
        or manifest.get("genindex_page_count") != index.get("genindex_page_count")
        or manifest.get("linked_page_count") != index.get("linked_page_count")
    ):
        errors.append("official manual recursive link-closure counts are inconsistent")
    converter = manifest.get("converter")
    if not isinstance(converter, dict):
        errors.append("snapshot converter identity is missing")
    else:
        expected_converter = {
            "adapter_path": "scripts/html2md_adapter.js",
            "adapter_schema_version": "1.0",
            "expected_upstream_commit": HTML2MD_COMMIT,
            "git_commit": HTML2MD_COMMIT,
            "project_name": "hello-html2md",
            "upstream_url": HTML2MD_UPSTREAM,
        }
        for key, value in expected_converter.items():
            if converter.get(key) != value:
                errors.append(f"snapshot converter identity mismatch: {key}")
        if converter.get("adapter_sha256") != sha256_file(DEFAULT_HTML2MD_ADAPTER):
            errors.append("snapshot html2md adapter hash mismatch")
        dependencies = converter.get("dependencies")
        if (
            not isinstance(dependencies, dict)
            or set(dependencies) != {"jsdom", "turndown", "turndown-plugin-gfm"}
        ):
            errors.append("snapshot converter dependency identity is incomplete")
    page_records = manifest.get("pages")
    indexed_pages = index.get("pages", [])
    mirrored_source_paths = {
        record.get("source_path")
        for record in page_records.values()
        if isinstance(record, dict)
    } if isinstance(page_records, dict) else set()
    if (
        not isinstance(page_records, dict)
        or mirrored_source_paths != set(indexed_pages)
    ):
        errors.append("mirrored pages do not equal the official index inventory")
        page_records = page_records if isinstance(page_records, dict) else {}
    if manifest.get("mirrored_page_count") != len(page_records):
        errors.append("mirrored page count does not match the manifest")
    curated_paths = {
        source_path(record, str(manifest.get("manual_version"))): topic
        for topic, record in registry["topics"].items()
    }
    if not set(curated_paths).issubset(mirrored_source_paths):
        errors.append("one or more curated entry points are absent from the full mirror")
    expected_files = {"manifest.json", "index.json", "manual-index.md"}
    records_by_source_path = {
        record.get("source_path"): record
        for record in page_records.values()
        if isinstance(record, dict)
    }
    for topic, record in page_records.items():
        filename = record.get("path")
        source_page = record.get("source_path")
        expected_filename = (
            markdown_path_for(source_page, curated_paths)
            if isinstance(source_page, str)
            else None
        )
        if not isinstance(filename, str) or filename != expected_filename:
            errors.append(f"invalid snapshot path for topic {topic}")
            continue
        expected_files.add(filename)
        path = snapshot_dir / filename
        if not path.is_file():
            errors.append(f"missing snapshot page for topic {topic}")
        elif sha256_file(path) != record.get("snapshot_sha256"):
            errors.append(f"snapshot hash mismatch for topic {topic}")
        else:
            try:
                markdown = path.read_text(encoding="utf-8", errors="strict")
            except (OSError, UnicodeDecodeError):
                errors.append(f"snapshot page is not valid UTF-8 for topic {topic}")
            else:
                if "\ufffd" in markdown or PRIVATE_HEADERLINK in markdown:
                    errors.append(f"snapshot page contains invalid display characters: {topic}")
                if max((len(line) for line in markdown.splitlines()), default=0) > 20_000:
                    errors.append(f"snapshot page contains an unreadably long line: {topic}")
                expected_header = (
                    f"# CP2K official manual snapshot: {record.get('source_path')}\n\n"
                    f"- Source: {record.get('source_url')}\n"
                    f"- Raw SHA-256: {record.get('raw_sha256')}\n"
                )
                if not markdown.startswith(expected_header):
                    errors.append(f"snapshot provenance header mismatch for topic {topic}")
        quality = record.get("conversion_quality")
        if (
            not isinstance(quality, dict)
            or quality.get("status") != "pass"
            or quality.get("token_sequence_preserved") is not True
            or quality.get("non_ascii_characters_preserved") is not True
            or quality.get("replacement_characters") != 0
            or quality.get("sphinx_private_header_glyphs") != 0
            or not isinstance(quality.get("max_line_chars"), int)
            or quality["max_line_chars"] > 20_000
        ):
            errors.append(f"snapshot conversion quality is incomplete for topic {topic}")
            continue
        if (
            not isinstance(quality.get("anchor_count"), int)
            or quality["anchor_count"] < 0
            or not isinstance(quality.get("internal_link_count"), int)
            or quality["internal_link_count"] < 0
        ):
            errors.append(f"snapshot link-closure counts are malformed for topic {topic}")
    known_paths = {
        record["path"]: record
        for record in page_records.values()
        if isinstance(record, dict) and isinstance(record.get("path"), str)
    }
    anchors_by_path: dict[str, set[str]] = {}
    markdown_by_path: dict[str, str] = {}
    for relative_path in known_paths:
        path = snapshot_dir / relative_path
        try:
            markdown = path.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeError):
            continue
        markdown_by_path[relative_path] = markdown
        anchors_by_path[relative_path] = {
            unquote(value)
            for value in re.findall(r'<a id="([^"]+)"></a>', markdown)
        }
    observed_internal_links = 0
    for relative_path, markdown in markdown_by_path.items():
        source_directory = posixpath.dirname(relative_path) or "."
        for href in re.findall(r"(?<!!)\[[^\]]*\]\(([^)\s]+)", markdown):
            href = href.strip("<>")
            if urlsplit(href).scheme or href.startswith("//"):
                continue
            target_part, fragment = urldefrag(href)
            if not target_part:
                target_path = relative_path
            else:
                target_path = posixpath.normpath(
                    posixpath.join(source_directory, unquote(target_part))
                )
            if target_path not in known_paths:
                errors.append(
                    f"unresolved local Markdown link: {relative_path} -> {href}"
                )
                continue
            observed_internal_links += 1
            if fragment and unquote(fragment) not in anchors_by_path.get(target_path, set()):
                errors.append(
                    f"unresolved local Markdown anchor: {relative_path} -> {href}"
                )
    if manifest.get("internal_link_count") != observed_internal_links:
        errors.append(
            "manifest internal link count does not match exact Markdown bytes"
        )
    actual_files = {
        path.relative_to(snapshot_dir).as_posix()
        for path in snapshot_dir.rglob("*")
        if path.is_file()
    }
    if actual_files != expected_files:
        errors.append("snapshot contains missing or unmanifested files")
    return {
        "schema_version": "2.0",
        "status": "ok" if not errors else "blocked",
        "manual_version": manifest.get("manual_version"),
        "manual_branch": manifest.get("manual_branch"),
        "index_page_count": index.get("page_count"),
        "genindex_page_count": index.get("genindex_page_count"),
        "linked_page_count": index.get("linked_page_count"),
        "mirrored_page_count": len(page_records),
        "mirrored_topic_count": len(page_records),
        "internal_link_count": sum(
            record.get("conversion_quality", {}).get("internal_link_count", 0)
            for record in page_records.values()
        ),
        "errors": errors,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refresh", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--version", default="2026.2")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--html2md-adapter", type=Path, default=DEFAULT_HTML2MD_ADAPTER)
    parser.add_argument("--html2md-root", type=Path, default=DEFAULT_HTML2MD_ROOT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.refresh:
            result = refresh_snapshot(
                args.version,
                registry_path=args.registry,
                snapshot_dir=args.snapshot,
                workers=args.workers,
                adapter_path=args.html2md_adapter,
                html2md_root=args.html2md_root,
            )
            summary = {
                "status": "ok",
                "manual_version": result["manual_version"],
                "index_page_count": result["index_page_count"],
                "mirrored_topic_count": result["mirrored_topic_count"],
            }
        else:
            summary = check_snapshot(registry_path=args.registry, snapshot_dir=args.snapshot)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
