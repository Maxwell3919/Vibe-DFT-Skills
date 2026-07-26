#!/usr/bin/env python3
"""Build or verify the complete SIESTA 5.4 official documentation mirror."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import posixpath
import re
import shutil
import subprocess
import tarfile
import tempfile
from typing import Any
from urllib.parse import unquote, urldefrag, urljoin, urlsplit
from urllib.request import Request, urlopen


SKILL_ROOT = Path(__file__).resolve().parent.parent
REFERENCES = SKILL_ROOT / "references"
DEFAULT_CACHE_ROOT = (
    Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    / "vibe-dft-skills"
    / "official-provider-mirrors"
    / "siesta-rigorous-calculations"
)
DEFAULT_SNAPSHOT = DEFAULT_CACHE_ROOT / "provider-snapshot"
DEFAULT_HTML2MD_ADAPTER = (
    SKILL_ROOT.parent
    / "cp2k-rigorous-calculations"
    / "scripts"
    / "html2md_adapter.js"
)
DEFAULT_HTML2MD_ROOT = Path(
    os.environ.get("HTML2MD_ROOT", Path.home() / ".local" / "share" / "html2md")
)
DEFAULT_SPHINX = (
    Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    / "vibe-dft-skills"
    / "manual-converter-venv"
    / "bin"
    / "sphinx-build"
)
SOURCE_COMMIT = "ca6da4c46538bccce34776cdbb075fa4bfc2c6dc"
SOURCE_REPOSITORY = "https://gitlab.com/siesta-project/documentation/siesta-docs"
SOURCE_ARCHIVE = (
    f"{SOURCE_REPOSITORY}/-/archive/{SOURCE_COMMIT}/"
    f"siesta-docs-{SOURCE_COMMIT}.tar.gz"
)
OFFICIAL_ROOT = "https://docs.siesta-project.org/projects/siesta/en/5.4/"
HTML2MD_COMMIT = "ca08965af93e6565806a79087868daa439565ffc"
MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
WORD_TOKEN = re.compile(r"\w+", flags=re.UNICODE)
SPHINX_UTILITY_PAGES = {"genindex.html", "search.html"}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def archive_cache() -> Path:
    path = (
        Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        / "vibe-dft-skills"
        / "official-source-archives"
        / f"siesta-docs-{SOURCE_COMMIT}.tar.gz"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def download_archive() -> Path:
    cache = archive_cache()
    if cache.is_file():
        try:
            with tarfile.open(cache, "r:gz"):
                return cache
        except (OSError, tarfile.TarError):
            cache.unlink()
    request = Request(
        SOURCE_ARCHIVE,
        headers={"User-Agent": "Vibe-DFT-Skills-SIESTA-manual-mirror/2.0"},
    )
    with urlopen(request, timeout=180) as response:
        body = response.read(MAX_ARCHIVE_BYTES + 1)
    if len(body) > MAX_ARCHIVE_BYTES:
        raise ValueError("SIESTA documentation archive exceeds the configured limit")
    temporary = cache.with_name(f".{cache.name}.stage-{os.getpid()}")
    temporary.write_bytes(body)
    with tarfile.open(temporary, "r:gz"):
        pass
    os.replace(temporary, cache)
    return cache


def extract_archive(archive: Path, target: Path) -> Path:
    roots: set[str] = set()
    with tarfile.open(archive, "r:gz") as handle:
        for member in handle:
            parts = Path(member.name).parts
            if not parts:
                continue
            roots.add(parts[0])
            relative = Path(*parts[1:])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("unsafe path in SIESTA documentation archive")
            if member.isdir():
                (target / relative).mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                continue
            source = handle.extractfile(member)
            if source is None:
                raise ValueError(f"cannot read archived source: {member.name}")
            output = target / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(source.read())
    if len(roots) != 1 or not (target / "docs" / "conf.py").is_file():
        raise ValueError("SIESTA documentation archive has an unexpected layout")
    return target / "docs"


def html2md_identity(adapter: Path, html2md_root: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            "node",
            str(adapter),
            "--html2md-root",
            str(html2md_root),
            "--identity",
        ],
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"html2md identity failed: {result.stderr.strip()}")
    identity = json.loads(result.stdout)
    if identity.get("git_commit") != HTML2MD_COMMIT:
        raise ValueError("html2md checkout does not match the pinned commit")
    return identity


def run_html2md(
    html: str,
    *,
    adapter: Path,
    html2md_root: Path,
) -> str:
    result = subprocess.run(
        ["node", str(adapter), "--html2md-root", str(html2md_root)],
        input=html,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"html2md conversion failed: {result.stderr.strip()}")
    markdown = result.stdout.replace("\r\n", "\n").replace("\r", "\n")
    if not markdown.strip() or "\ufffd" in markdown:
        raise ValueError("html2md produced empty or damaged Markdown")
    return markdown.strip() + "\n"


def output_path_for(html_path: str) -> str:
    if html_path == "index.html":
        return "home.md"
    if html_path == "reference/siesta.html":
        return "siesta.md"
    path = Path(html_path)
    if path.is_absolute() or ".." in path.parts or path.suffix != ".html":
        raise ValueError(f"unsafe generated SIESTA page path: {html_path}")
    return (Path("pages") / path.with_suffix(".md")).as_posix()


def prepare_article(
    html_path: str,
    body: bytes,
    output_paths: dict[str, str],
) -> tuple[str, str, list[dict[str, str]], list[str]]:
    try:
        from bs4 import BeautifulSoup
    except ModuleNotFoundError as exc:
        raise RuntimeError("beautifulsoup4 is required for the SIESTA mirror") from exc
    source = body.decode("utf-8", errors="strict")
    if "\ufffd" in source:
        raise ValueError(f"replacement character in generated HTML: {html_path}")
    soup = BeautifulSoup(source, "lxml")
    article = (
        soup.find("div", attrs={"role": "main"})
        or soup.find("main")
        or soup.find("article")
    )
    if article is None:
        raise ValueError(f"no main content in generated SIESTA page: {html_path}")
    for node in article.find_all(["script", "style", "nav", "form"]):
        node.decompose()
    for node in article.select("a.headerlink, .headerlink"):
        node.decompose()
    anchors: list[str] = []
    seen: set[str] = set()
    anchor_nodes = [article] + list(article.find_all(attrs={"id": True}))
    for node in anchor_nodes:
        anchor_id = node.get("id")
        if not isinstance(anchor_id, str) or not anchor_id or anchor_id in seen:
            continue
        anchor = soup.new_tag("a")
        anchor["id"] = anchor_id
        anchor["data-cp2k-manual-anchor"] = "true"
        node.insert(0, anchor)
        anchors.append(anchor_id)
        seen.add(anchor_id)
    source_output = output_paths[html_path]
    source_url = urljoin(OFFICIAL_ROOT, html_path)
    links: list[dict[str, str]] = []
    for node in article.find_all(True):
        href = node.get("href")
        if isinstance(href, str) and href:
            if href == "run:tbtrans.pdf":
                absolute = urljoin(OFFICIAL_ROOT, "reference/tbtrans.html")
            else:
                absolute = urljoin(source_url, href)
            target_url, fragment = urldefrag(absolute)
            if target_url.startswith(OFFICIAL_ROOT) and target_url.endswith(".html"):
                target_html = unquote(target_url.removeprefix(OFFICIAL_ROOT))
                fragment = unquote(fragment)
                target_output = output_paths.get(target_html)
                if target_output is None:
                    raise ValueError(
                        f"internal SIESTA link is outside the generated inventory: {target_html}"
                    )
                if target_output == source_output:
                    local = ""
                else:
                    local = posixpath.relpath(
                        target_output,
                        start=posixpath.dirname(source_output) or ".",
                    )
                local_href = local + (f"#{fragment}" if fragment else "")
                node["href"] = local_href or Path(target_output).name
                links.append(
                    {
                        "target_html_path": target_html,
                        "target_markdown_path": target_output,
                        "fragment": fragment,
                        "local_href": node["href"],
                    }
                )
            else:
                node["href"] = absolute
        src = node.get("src")
        if isinstance(src, str) and src:
            node["src"] = urljoin(source_url, src)
    source_text = article.get_text()
    if len(WORD_TOKEN.findall(source_text)) < 2:
        raise ValueError(f"generated SIESTA page is unexpectedly empty: {html_path}")
    return str(article), source_text, links, anchors


def conversion_quality(source_text: str, markdown: str, page: str) -> dict[str, Any]:
    source_tokens = WORD_TOKEN.findall(source_text.casefold())
    normalized_markdown = re.sub(
        r"\\([\\`*_{}\[\]()#+\-.!<>])",
        r"\1",
        markdown,
    )
    normalized_markdown = re.sub(r"(?<!\\)\*", "", normalized_markdown)
    # Sphinx syntax highlighting can split one identifier across adjacent
    # spans, while Turndown correctly rejoins it. Conversely Markdown emphasis
    # can split one HTML text run. Compare the ordered alphanumeric character
    # stream so those representation-only boundaries do not create false loss.
    source_characters = [
        character.casefold()
        for character in source_text
        if character.isalnum()
    ]
    markdown_characters = iter(
        character.casefold()
        for character in normalized_markdown
        if character.isalnum()
    )
    for source_character in source_characters:
        for markdown_character in markdown_characters:
            if markdown_character == source_character:
                break
        else:
            raise ValueError(
                f"Markdown lost or reordered visible characters in {page}"
            )
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
    missing = {
        character: count - markdown_non_ascii[character]
        for character, count in source_non_ascii.items()
        if markdown_non_ascii[character] < count
    }
    if missing:
        raise ValueError(f"Markdown lost non-ASCII characters in {page}: {missing}")
    max_line = max((len(line) for line in markdown.splitlines()), default=0)
    if max_line > 20_000:
        raise ValueError(f"unreadably long Markdown line in {page}")
    return {
        "status": "pass",
        "source_text_sha256": sha256_bytes(source_text.encode("utf-8")),
        "source_token_count": len(source_tokens),
        "source_alphanumeric_character_count": len(source_characters),
        "source_non_ascii_chars": sum(source_non_ascii.values()),
        "token_sequence_preserved": True,
        "non_ascii_characters_preserved": True,
        "replacement_characters": 0,
        "max_line_chars": max_line,
    }


def build_sphinx(source: Path, output: Path, sphinx: Path) -> dict[str, Any]:
    if not sphinx.is_file():
        raise RuntimeError(
            f"Sphinx is missing: {sphinx}; install the exact upstream docs/requirements.txt"
        )
    result = subprocess.run(
        [str(sphinx), "-b", "html", "-E", "-a", str(source), str(output)],
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=900,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"SIESTA Sphinx build failed:\n{result.stdout[-8000:]}")
    source_prefix = str(source) + "/"
    output_prefix = str(output) + "/"
    warnings = [
        line.replace(source_prefix, "<source>/").replace(output_prefix, "<output>/")
        for line in result.stdout.splitlines()
        if "WARNING:" in line
    ]
    return {
        "command": "sphinx-build -b html -E -a",
        "executable": sphinx.name,
        "version": subprocess.run(
            [str(sphinx), "--version"],
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
        ).stdout.strip(),
        "warnings": warnings,
    }


def refresh(
    *,
    snapshot: Path,
    adapter: Path,
    html2md_root: Path,
    sphinx: Path,
) -> dict[str, Any]:
    identity = html2md_identity(adapter, html2md_root)
    archive = download_archive()
    retrieved = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    with tempfile.TemporaryDirectory(prefix="siesta-manual-build-") as temporary:
        temporary_path = Path(temporary)
        source = extract_archive(archive, temporary_path / "source")
        built = temporary_path / "html"
        sphinx_identity = build_sphinx(source, built, sphinx)
        all_html_files = sorted(
            path
            for path in built.rglob("*.html")
            if "_static" not in path.relative_to(built).parts
        )
        excluded_utility_pages = sorted(
            path.relative_to(built).as_posix()
            for path in all_html_files
            if path.relative_to(built).as_posix() in SPHINX_UTILITY_PAGES
        )
        html_files = [
            path
            for path in all_html_files
            if path.relative_to(built).as_posix() not in SPHINX_UTILITY_PAGES
        ]
        html_paths = [path.relative_to(built).as_posix() for path in html_files]
        source_pages = {
            path.relative_to(source).with_suffix("").as_posix()
            for path in source.rglob("*")
            if path.is_file() and path.suffix.casefold() in {".rst", ".md"}
        }
        rendered_source_pages = {
            Path(path).with_suffix("").as_posix()
            for path in html_paths
        }
        missing_sources = source_pages - rendered_source_pages
        output_paths = {path: output_path_for(path) for path in html_paths}
        if len(set(output_paths.values())) != len(output_paths):
            raise ValueError("SIESTA Markdown output mapping is not one-to-one")
        stage = temporary_path / "official-manual"
        stage.mkdir()
        pages: dict[str, Any] = {}
        for source_file, html_path in zip(html_files, html_paths, strict=True):
            raw = source_file.read_bytes()
            article, source_text, links, anchors = prepare_article(
                html_path,
                raw,
                output_paths,
            )
            converted = run_html2md(
                article,
                adapter=adapter,
                html2md_root=html2md_root,
            )
            output_path = output_paths[html_path]
            official_url = urljoin(OFFICIAL_ROOT, html_path)
            markdown = (
                f"# SIESTA 5.4 official documentation: {html_path}\n\n"
                f"- Official page: <{official_url}>\n"
                f"- Official source repository: <{SOURCE_REPOSITORY}/-/tree/{SOURCE_COMMIT}/docs>\n"
                f"- Source commit: `{SOURCE_COMMIT}`\n"
                f"- Generated HTML SHA-256: `{sha256_bytes(raw)}`\n"
                f"- Converter: `helloworld-Co/html2md` at `{HTML2MD_COMMIT}`\n\n"
                "---\n\n"
                + converted
            )
            quality = conversion_quality(source_text, markdown, html_path)
            quality["anchors"] = anchors
            quality["internal_links"] = links
            output = stage / output_path
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(markdown, encoding="utf-8", newline="\n")
            pages[html_path] = {
                "html_path": html_path,
                "markdown_path": output_path,
                "official_url": official_url,
                "generated_html_bytes": len(raw),
                "generated_html_sha256": sha256_bytes(raw),
                "markdown_bytes": output.stat().st_size,
                "markdown_sha256": sha256_file(output),
                "conversion_quality": quality,
            }
        compatibility_aliases: dict[str, set[str]] = {}
        for source_record in pages.values():
            for link in source_record["conversion_quality"]["internal_links"]:
                fragment = link["fragment"]
                target_html = link["target_html_path"]
                if (
                    fragment
                    and fragment
                    not in pages[target_html]["conversion_quality"]["anchors"]
                ):
                    compatibility_aliases.setdefault(target_html, set()).add(fragment)
        for target_html, fragments in sorted(compatibility_aliases.items()):
            record = pages[target_html]
            output = stage / record["markdown_path"]
            aliases = sorted(fragments)
            alias_block = "\n".join(
                f'<a id="{html.escape(fragment, quote=True)}"></a>'
                for fragment in aliases
            )
            original = output.read_text(encoding="utf-8")
            marker = "\n---\n\n"
            if marker not in original:
                raise ValueError(
                    f"cannot place SIESTA compatibility anchors: {target_html}"
                )
            note = (
                "\n<!-- Local compatibility anchors for fragments referenced by "
                "the official generated HTML but absent from its emitted IDs. -->\n"
                f"{alias_block}\n"
            )
            updated = original.replace(marker, note + marker, 1)
            output.write_text(updated, encoding="utf-8", newline="\n")
            quality = record["conversion_quality"]
            quality["compatibility_anchor_aliases"] = aliases
            quality["anchors"].extend(aliases)
            record["markdown_bytes"] = output.stat().st_size
            record["markdown_sha256"] = sha256_file(output)
        for target_html, record in pages.items():
            record["conversion_quality"].setdefault(
                "compatibility_anchor_aliases", []
            )
        source_only_pages: dict[str, Any] = {}
        for source_stem in sorted(missing_sources):
            matches = [
                path
                for suffix in (".md", ".rst")
                if (path := source / f"{source_stem}{suffix}").is_file()
            ]
            if len(matches) != 1:
                raise ValueError(f"cannot resolve source-only document: {source_stem}")
            source_file = matches[0]
            raw = source_file.read_bytes()
            text = raw.decode("utf-8", errors="strict")
            if "\ufffd" in text or "\x00" in text:
                raise ValueError(f"invalid characters in source-only document: {source_stem}")
            relative_source = source_file.relative_to(source).as_posix()
            output_path = (
                Path("source-only") / Path(relative_source).with_suffix(".md")
            ).as_posix()
            source_url = (
                f"{SOURCE_REPOSITORY}/-/blob/{SOURCE_COMMIT}/docs/{relative_source}"
            )
            markdown = (
                f"# SIESTA official source documentation: {relative_source}\n\n"
                f"- Official source: <{source_url}>\n"
                f"- Source commit: `{SOURCE_COMMIT}`\n"
                f"- Conversion: `identity-markdown`\n\n"
                "---\n\n"
                + text.rstrip()
                + "\n"
            )
            output = stage / output_path
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(markdown, encoding="utf-8", newline="\n")
            source_only_pages[relative_source] = {
                "source_path": relative_source,
                "markdown_path": output_path,
                "official_url": source_url,
                "raw_bytes": len(raw),
                "raw_sha256": sha256_bytes(raw),
                "markdown_bytes": output.stat().st_size,
                "markdown_sha256": sha256_file(output),
                "conversion": "identity-markdown",
                "replacement_characters": 0,
                "internal_links": [],
            }
        ford_root = Path("source-only/background/ford-pages")
        ford_link = re.compile(
            r"(?P<prefix>\]\()\|page\|/(?P<target>[^)#]+?)\.html"
            r"(?P<fragment>#[^)]*)?(?P<suffix>\))"
        )
        ford_media = re.compile(
            r"!\[[^\]]*\]\(\|media\|/[^)\s]+(?:\s+\"[^\"]*\")?\)",
            flags=re.DOTALL,
        )
        for source_path, record in source_only_pages.items():
            output = stage / record["markdown_path"]
            text = output.read_text(encoding="utf-8")
            receipts: list[dict[str, str]] = []

            def replace_ford_link(match: re.Match[str]) -> str:
                target = (ford_root / f"{match.group('target')}.md").as_posix()
                target_output = stage / target
                if not target_output.is_file():
                    raise ValueError(
                        f"unresolved SIESTA source-only Ford link: "
                        f"{source_path} -> {target}"
                    )
                local = posixpath.relpath(
                    target,
                    start=posixpath.dirname(record["markdown_path"]) or ".",
                )
                fragment = match.group("fragment") or ""
                receipts.append(
                    {
                        "target_markdown_path": target,
                        "fragment": fragment.removeprefix("#"),
                        "local_href": local + fragment,
                    }
                )
                return (
                    match.group("prefix")
                    + local
                    + fragment
                    + match.group("suffix")
                )

            rewritten = ford_link.sub(replace_ford_link, text)
            unavailable_assets: list[str] = []

            def preserve_unavailable_media(match: re.Match[str]) -> str:
                literal = match.group(0)
                media = re.search(r"\|media\|/[^)\s]+", literal)
                assert media is not None
                unavailable_assets.append(media.group(0))
                return (
                    "> The pinned official SIESTA documentation source references "
                    "this media asset, but the exact source tree contains no "
                    "corresponding file. The original reference is preserved "
                    "verbatim below.\n\n"
                    "```markdown\n"
                    + literal
                    + "\n```\n"
                )

            rewritten = ford_media.sub(preserve_unavailable_media, rewritten)
            if rewritten != text:
                output.write_text(rewritten, encoding="utf-8", newline="\n")
                record["markdown_bytes"] = output.stat().st_size
                record["markdown_sha256"] = sha256_file(output)
            record["internal_links"] = receipts
            record["upstream_unavailable_media_assets"] = sorted(
                unavailable_assets
            )
        index_lines = [
            "# SIESTA 5.4 complete official documentation mirror",
            "",
            f"- Official root: <{OFFICIAL_ROOT}>",
            f"- Exact source commit: `{SOURCE_COMMIT}`",
            f"- Rendered documentation pages: {len(pages)}",
            f"- Source-only documentation pages: {len(source_only_pages)}",
            f"- Internal links checked: {sum(len(record['conversion_quality']['internal_links']) for record in pages.values())}",
            f"- Upstream-missing fragment aliases: {sum(len(values) for values in compatibility_aliases.values())}",
            "",
            "## Rendered pages",
            "",
        ]
        for html_path, record in sorted(pages.items()):
            index_lines.append(f"- [{html_path}]({record['markdown_path']})")
        index_lines.extend(["", "## Source-only pages", ""])
        for source_path, record in sorted(source_only_pages.items()):
            index_lines.append(f"- [{source_path}]({record['markdown_path']})")
        manual_index = "\n".join(index_lines).rstrip() + "\n"
        (stage / "manual-index.md").write_text(
            manual_index,
            encoding="utf-8",
            newline="\n",
        )
        source_files = sorted(
            path.relative_to(source).as_posix()
            for path in source.rglob("*")
            if path.is_file() and path.suffix.casefold() in {".rst", ".md"}
        )
        manifest = {
            "schema_version": "1.0",
            "documentation_line": "5.4",
            "retrieved_utc": retrieved,
            "official_root": OFFICIAL_ROOT,
            "source_repository": SOURCE_REPOSITORY,
            "source_commit": SOURCE_COMMIT,
            "source_archive": SOURCE_ARCHIVE,
            "source_archive_sha256": sha256_file(archive),
            "manual_index_sha256": sha256_bytes(manual_index.encode("utf-8")),
            "source_document_count": len(source_files),
            "source_documents": source_files,
            "source_only_page_count": len(source_only_pages),
            "source_only_internal_link_count": sum(
                len(record["internal_links"])
                for record in source_only_pages.values()
            ),
            "excluded_generated_utility_pages": excluded_utility_pages,
            "rendered_page_count": len(pages),
            "mirrored_page_count": len(pages),
            "internal_link_count": sum(
                len(record["conversion_quality"]["internal_links"])
                for record in pages.values()
            ),
            "compatibility_anchor_alias_count": sum(
                len(values) for values in compatibility_aliases.values()
            ),
            "html2md_identity": identity,
            "html2md_adapter": {
                "path": str(adapter.relative_to(SKILL_ROOT.parent)),
                "sha256": sha256_file(adapter),
            },
            "sphinx": sphinx_identity,
            "pages": dict(sorted(pages.items())),
            "source_only_pages": dict(sorted(source_only_pages.items())),
        }
        (stage / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        backup = snapshot.with_name(snapshot.name + ".backup")
        if backup.exists():
            shutil.rmtree(backup)
        if snapshot.exists():
            snapshot.replace(backup)
        try:
            stage.replace(snapshot)
        except Exception:
            if backup.exists() and not snapshot.exists():
                backup.replace(snapshot)
            raise
        finally:
            if backup.exists():
                shutil.rmtree(backup)
    return check(snapshot=snapshot, adapter=adapter)


def check(*, snapshot: Path, adapter: Path) -> dict[str, Any]:
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    pages = manifest.get("pages")
    source_only_pages = manifest.get("source_only_pages")
    if manifest.get("schema_version") != "1.0" or not isinstance(pages, dict):
        errors.append("manifest schema is unsupported")
        pages = pages if isinstance(pages, dict) else {}
    if not isinstance(source_only_pages, dict):
        errors.append("source-only page inventory is malformed")
        source_only_pages = {}
    if manifest.get("source_commit") != SOURCE_COMMIT:
        errors.append("source commit mismatch")
    if manifest.get("mirrored_page_count") != len(pages):
        errors.append("mirrored page count mismatch")
    if manifest.get("source_document_count") != len(manifest.get("source_documents", [])):
        errors.append("source document count mismatch")
    if manifest.get("source_only_page_count") != len(source_only_pages):
        errors.append("source-only page count mismatch")
    excluded_utility_pages = manifest.get("excluded_generated_utility_pages", [])
    if (
        not isinstance(excluded_utility_pages, list)
        or not set(excluded_utility_pages).issubset(SPHINX_UTILITY_PAGES)
    ):
        errors.append("generated utility-page exclusion mismatch")
    if manifest.get("html2md_adapter", {}).get("sha256") != sha256_file(adapter):
        errors.append("html2md adapter hash mismatch")
    expected = {"manifest.json", "manual-index.md"}
    manual_index = snapshot / "manual-index.md"
    if (
        not manual_index.is_file()
        or manifest.get("manual_index_sha256") != sha256_file(manual_index)
    ):
        errors.append("human-readable manual index is missing or changed")
    for html_path, record in pages.items():
        markdown_path = record.get("markdown_path")
        if not isinstance(markdown_path, str) or markdown_path != output_path_for(html_path):
            errors.append(f"invalid output path: {html_path}")
            continue
        expected.add(markdown_path)
        output = snapshot / markdown_path
        if not output.is_file() or sha256_file(output) != record.get("markdown_sha256"):
            errors.append(f"missing or changed page: {html_path}")
            continue
        try:
            markdown = output.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeError):
            errors.append(f"page is not strict UTF-8: {html_path}")
            continue
        if "\ufffd" in markdown or "\x00" in markdown:
            errors.append(f"page contains invalid display characters: {html_path}")
        quality = record.get("conversion_quality")
        if (
            not isinstance(quality, dict)
            or quality.get("status") != "pass"
            or quality.get("token_sequence_preserved") is not True
            or quality.get("non_ascii_characters_preserved") is not True
        ):
            errors.append(f"conversion gate failed: {html_path}")
            continue
        for link in quality.get("internal_links", []):
            target_html = link.get("target_html_path")
            target = pages.get(target_html)
            fragment = link.get("fragment")
            if not isinstance(target, dict) or not (snapshot / target["markdown_path"]).is_file():
                errors.append(f"unresolved internal link: {html_path} -> {target_html}")
                continue
            if fragment and fragment not in target["conversion_quality"].get("anchors", []):
                errors.append(
                    f"unresolved internal anchor: {html_path} -> {target_html}#{fragment}"
                )
    for source_path, record in source_only_pages.items():
        markdown_path = record.get("markdown_path")
        expected_path = (
            Path("source-only") / Path(source_path).with_suffix(".md")
        ).as_posix()
        if not isinstance(markdown_path, str) or markdown_path != expected_path:
            errors.append(f"invalid source-only output path: {source_path}")
            continue
        expected.add(markdown_path)
        output = snapshot / markdown_path
        if not output.is_file() or sha256_file(output) != record.get("markdown_sha256"):
            errors.append(f"missing or changed source-only page: {source_path}")
            continue
        try:
            text = output.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeError):
            errors.append(f"source-only page is not strict UTF-8: {source_path}")
            continue
        if "\ufffd" in text or "\x00" in text:
            errors.append(f"source-only page contains invalid characters: {source_path}")
        if "|page|/" in text:
            errors.append(f"source-only page retains unresolved Ford links: {source_path}")
        unavailable_assets = record.get("upstream_unavailable_media_assets", [])
        if (
            not isinstance(unavailable_assets, list)
            or any(
                not isinstance(asset, str) or not asset.startswith("|media|/")
                for asset in unavailable_assets
            )
            or text.count("|media|/") != len(unavailable_assets)
            or any(asset not in text for asset in unavailable_assets)
        ):
            errors.append(
                f"source-only page has unaccounted Ford media references: {source_path}"
            )
        for link in record.get("internal_links", []):
            target = link.get("target_markdown_path")
            if not isinstance(target, str) or not (snapshot / target).is_file():
                errors.append(
                    f"unresolved source-only internal link: {source_path} -> {target}"
                )
    actual = {
        path.relative_to(snapshot).as_posix()
        for path in snapshot.rglob("*")
        if path.is_file()
    }
    if actual != expected:
        errors.append("snapshot contains missing or unmanifested files")
    return {
        "schema_version": "1.0",
        "status": "ok" if not errors else "blocked",
        "source_document_count": manifest.get("source_document_count"),
        "source_only_page_count": len(source_only_pages),
        "mirrored_page_count": len(pages),
        "internal_link_count": sum(
            len(record.get("conversion_quality", {}).get("internal_links", []))
            for record in pages.values()
        ),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refresh", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--html2md-adapter", type=Path, default=DEFAULT_HTML2MD_ADAPTER)
    parser.add_argument("--html2md-root", type=Path, default=DEFAULT_HTML2MD_ROOT)
    parser.add_argument("--sphinx", type=Path, default=DEFAULT_SPHINX)
    args = parser.parse_args()
    try:
        if args.refresh:
            result = refresh(
                snapshot=args.snapshot,
                adapter=args.html2md_adapter,
                html2md_root=args.html2md_root,
                sphinx=args.sphinx,
            )
        else:
            result = check(snapshot=args.snapshot, adapter=args.html2md_adapter)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError, tarfile.TarError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
