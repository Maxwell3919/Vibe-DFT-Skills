#!/usr/bin/env python3
"""Mirror the complete VASP Wiki main namespace with link-closure checks."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import html
from html.parser import HTMLParser
import json
import os
import posixpath
import re
import shutil
import ssl
import sys
import subprocess
import tempfile
import time
import unicodedata
import urllib.parse
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


API_URL = "https://www.vasp.at/wiki/api.php"
OFFICIAL_ROOT = "https://www.vasp.at/wiki/"
DEFAULT_CACHE_ROOT = (
    Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    / "vibe-dft-skills"
    / "official-provider-mirrors"
    / "vasp-rigorous-calculations"
    / "provider-root"
)
DEFAULT_HTML2MD_ADAPTER = (
    Path(__file__).resolve().parents[2]
    / "cp2k-rigorous-calculations"
    / "scripts"
    / "html2md_adapter.js"
)
DEFAULT_HTML2MD_ROOT = Path(
    os.environ.get("HTML2MD_ROOT", Path.home() / ".local" / "share" / "html2md")
)
DEFAULT_RAW_CACHE = (
    Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    / "vibe-dft-skills"
    / "vasp-wiki-api"
)
HTML2MD_COMMIT = "ca08965af93e6565806a79087868daa439565ffc"
PUBLICLY_UNAVAILABLE_CODES = {"missingtitle", "permissiondenied"}
CATEGORIES = ("INCAR tag", "Input files", "Output files")
CORE_PAGES = (
    "Main page",
    "INCAR",
    "POSCAR",
    "KPOINTS",
    "POTCAR",
    "OUTCAR",
    "vasprun.xml",
    "OSZICAR",
    "CONTCAR",
    "CHGCAR",
    "WAVECAR",
    "IBZKPT",
    "PROCAR",
    "DOSCAR",
    "EIGENVAL",
    "XDATCAR",
    "Electronic minimization",
    "Structure optimization",
    "Smearing technique",
    "Band-structure calculation using hybrid functionals",
    "ENCUT",
    "PREC",
    "ENAUG",
    "LREAL",
    "ADDGRID",
    "LASPH",
    "LMAXMIX",
    "EDIFF",
    "NELM",
    "NELMIN",
    "ALGO",
    "IALGO",
    "ISMEAR",
    "SIGMA",
    "KSPACING",
    "KGAMMA",
    "ISYM",
    "SYMPREC",
    "IBRION",
    "NSW",
    "ISIF",
    "EDIFFG",
    "POTIM",
    "ISTART",
    "ICHARG",
    "LWAVE",
    "LCHARG",
    "LORBIT",
    "NEDOS",
    "EMIN",
    "EMAX",
    "NBANDS",
    "ISPIN",
    "MAGMOM",
    "LSORBIT",
    "LNONCOLLINEAR",
    "SAXIS",
    "LDAU",
    "LDAUTYPE",
    "LDAUL",
    "LDAUU",
    "LDAUJ",
    "LDAUPRINT",
    "GGA",
    "METAGGA",
    "IVDW",
    "LHFCALC",
    "HFSCREEN",
    "AEXX",
    "TIME",
    "NELECT",
    "LDIPOL",
    "IDIPOL",
    "DIPOL",
    "LEPSILON",
    "LCALCEPS",
    "LOPTICS",
    "LELF",
    "NCORE",
    "KPAR",
    "NWRITE",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def page_url(title: str) -> str:
    return OFFICIAL_ROOT + urllib.parse.quote(title.replace(" ", "_"), safe="/:()")


def slugify(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "page"


def request_json(params: dict[str, Any], attempts: int = 5) -> dict[str, Any]:
    query = urllib.parse.urlencode({**params, "format": "json", "formatversion": "2"})
    request = urllib.request.Request(
        f"{API_URL}?{query}",
        headers={"User-Agent": "Vibe-DFT-Skills-VASP-mirror/1.0 (official documentation mirror)"},
    )
    transient = (urllib.error.URLError, TimeoutError, ConnectionError, ssl.SSLError)
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except transient:
            if attempt == attempts:
                raise
            time.sleep(min(2 ** (attempt - 1), 8))
    raise RuntimeError("unreachable retry state")


def category_titles(category: str) -> list[str]:
    titles: list[str] = []
    continuation: str | None = None
    while True:
        params: dict[str, Any] = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmnamespace": 0,
            "cmlimit": "max",
        }
        if continuation:
            params["cmcontinue"] = continuation
        data = request_json(params)
        titles.extend(item["title"] for item in data["query"]["categorymembers"])
        continuation = data.get("continue", {}).get("cmcontinue")
        if not continuation:
            return titles


def all_main_namespace_titles() -> list[str]:
    """Enumerate every main-namespace title, including redirect aliases."""

    titles: list[str] = []
    continuation: str | None = None
    while True:
        params: dict[str, Any] = {
            "action": "query",
            "list": "allpages",
            "apnamespace": 0,
            "aplimit": "max",
            "apfilterredir": "all",
        }
        if continuation:
            params["apcontinue"] = continuation
        data = request_json(params)
        titles.extend(item["title"] for item in data["query"]["allpages"])
        continuation = data.get("continue", {}).get("apcontinue")
        if not continuation:
            return sorted(set(titles))


class SearchableTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self.skip += 1
            return
        if self.skip:
            return
        if tag in {"h1", "h2", "h3", "h4", "h5", "p", "div", "tr", "pre", "table"}:
            self.parts.append("\n")
        if tag == "li":
            self.parts.append("\n- ")
        if tag == "br":
            self.parts.append("\n")
        if tag == "img":
            alt = dict(attrs).get("alt")
            if alt:
                self.parts.append(alt)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self.skip = max(0, self.skip - 1)
        elif not self.skip and tag in {"p", "div", "li", "tr", "pre", "h1", "h2", "h3", "h4", "h5"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip:
            self.parts.append(data)

    def text(self) -> str:
        value = html.unescape("".join(self.parts)).replace("\xa0", " ")
        value = re.sub(r"[ \t]+", " ", value)
        value = re.sub(r" *\n *", "\n", value)
        value = re.sub(r"\n{3,}", "\n\n", value)
        return value.strip() + "\n"


def html_to_text(source: str) -> str:
    parser = SearchableTextParser()
    parser.feed(source)
    return parser.text()


def html2md_identity() -> dict[str, Any]:
    result = subprocess.run(
        [
            "node",
            str(DEFAULT_HTML2MD_ADAPTER),
            "--html2md-root",
            str(DEFAULT_HTML2MD_ROOT),
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


def run_html2md(source: str) -> str:
    result = subprocess.run(
        [
            "node",
            str(DEFAULT_HTML2MD_ADAPTER),
            "--html2md-root",
            str(DEFAULT_HTML2MD_ROOT),
        ],
        input=source,
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
        raise ValueError("html2md emitted empty or damaged Markdown")
    return markdown.strip() + "\n"


def prepare_page_html(
    page: dict[str, Any],
    title_paths: dict[str, str],
) -> tuple[str, str, list[dict[str, str]], list[str]]:
    try:
        from bs4 import BeautifulSoup
    except ModuleNotFoundError as exc:
        raise RuntimeError("beautifulsoup4 is required for the VASP Wiki mirror") from exc
    soup = BeautifulSoup(page["html"], "lxml")
    for node in soup.find_all(["script", "style", "noscript", "form"]):
        node.decompose()
    for node in soup.select(".mw-editsection, .mw-cite-backlink"):
        node.decompose()
    # GFM tables cannot represent HTML colspan/rowspan. Turndown otherwise
    # emits the entire table as one raw-HTML line. Expand colspan cells with
    # empty siblings and drop rowspan presentation metadata so the exact text
    # remains readable as ordinary Markdown rows.
    for cell in soup.select("th[colspan], td[colspan]"):
        try:
            span = max(1, int(cell.get("colspan", "1")))
        except (TypeError, ValueError):
            span = 1
        cell.attrs.pop("colspan", None)
        for _ in range(span - 1):
            empty = soup.new_tag(cell.name)
            cell.insert_after(empty)
    for cell in soup.select("th[rowspan], td[rowspan]"):
        cell.attrs.pop("rowspan", None)
    for table in soup.find_all("table"):
        rows = table.find_all("tr", recursive=True)
        if (
            len(rows) >= 2
            and rows[0].find("th") is None
            and rows[1].find("th") is not None
        ):
            label = soup.new_tag("p")
            label.string = rows[0].get_text(" ", strip=True)
            table.insert_before(label)
            rows[0].decompose()
            rows = table.find_all("tr", recursive=True)
        # MediaWiki commonly emits semantic table headers as ordinary td
        # cells. Turndown's GFM plugin only recognizes a Markdown table when
        # the first row contains th cells; otherwise it preserves the entire
        # table as raw HTML. Promote that first row without changing its text.
        if rows and rows[0].find("th") is None:
            for cell in rows[0].find_all("td", recursive=False):
                cell.name = "th"
    anchors: list[str] = []
    seen: set[str] = set()
    for node in list(soup.find_all(attrs={"id": True})):
        anchor_id = node.get("id")
        if not isinstance(anchor_id, str) or not anchor_id or anchor_id in seen:
            continue
        anchor = soup.new_tag("a")
        anchor["id"] = anchor_id
        anchor["data-cp2k-manual-anchor"] = "true"
        node.insert_before(anchor)
        anchors.append(anchor_id)
        seen.add(anchor_id)
    links: list[dict[str, str]] = []
    current_path = title_paths[f"exact:{page['title']}"]
    for node in soup.find_all(True):
        href = node.get("href")
        if isinstance(href, str) and href:
            absolute = urllib.parse.urljoin(page_url(page["title"]), href)
            target_url, fragment = urllib.parse.urldefrag(absolute)
            parsed = urllib.parse.urlsplit(target_url)
            if (
                parsed.scheme == "https"
                and parsed.netloc in {"vasp.at", "www.vasp.at"}
                and parsed.path.startswith("/wiki/")
            ):
                target_title = urllib.parse.unquote(
                    parsed.path.removeprefix("/wiki/")
                ).replace("_", " ")
                target_path = title_paths.get(f"exact:{target_title}")
                if target_path is None:
                    target_path = title_paths.get(f"fold:{target_title.casefold()}")
                if target_path is not None:
                    local = "" if target_path == current_path else target_path
                    node["href"] = local + (f"#{fragment}" if fragment else "")
                    if not node["href"]:
                        node["href"] = current_path
                    links.append(
                        {
                            "target_title": target_title,
                            "target_markdown_path": target_path,
                            "fragment": fragment,
                            "local_href": node["href"],
                        }
                    )
                    continue
            node["href"] = absolute
        src = node.get("src")
        if isinstance(src, str) and src:
            node["src"] = urllib.parse.urljoin(page_url(page["title"]), src)
    source_text = soup.get_text()
    return str(soup), source_text, links, anchors


def conversion_quality(source_text: str, markdown: str, title: str) -> dict[str, Any]:
    token = re.compile(r"\w+", flags=re.UNICODE)
    source_tokens = token.findall(source_text.casefold())
    normalized_markdown = re.sub(
        r"\\([\\`*_{}\[\]()#+\-.!<>])",
        r"\1",
        markdown,
    )
    normalized_markdown = re.sub(r"(?<!\\)\*", "", normalized_markdown)
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
                f"Markdown lost or reordered official visible characters: {title}"
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
        raise ValueError(f"Markdown lost non-ASCII characters: {title}: {missing}")
    max_line = max((len(line) for line in markdown.splitlines()), default=0)
    if max_line > 20_000:
        raise ValueError(f"Markdown contains an unreadably long line: {title}")
    return {
        "status": "pass",
        "token_sequence_preserved": True,
        "non_ascii_characters_preserved": True,
        "replacement_characters": 0,
        "source_token_count": len(source_tokens),
        "source_alphanumeric_character_count": len(source_characters),
        "source_text_sha256": sha256_bytes(source_text.encode("utf-8")),
        "max_line_chars": max_line,
    }


class PublicPageUnavailable(RuntimeError):
    def __init__(self, title: str, error: dict[str, Any]) -> None:
        super().__init__(f"{title}: {error}")
        self.title = title
        self.code = str(error.get("code", "unknown"))
        self.info = str(error.get("info", ""))


def fetch_page(title: str) -> dict[str, Any]:
    cache = DEFAULT_RAW_CACHE / f"{sha256_bytes(title.encode('utf-8'))}.json"
    if cache.is_file() and time.time() - cache.stat().st_mtime < 3600:
        try:
            cached = json.loads(cache.read_text(encoding="utf-8"))
            if cached.get("requested_title") == title:
                return cached
        except (OSError, UnicodeError, json.JSONDecodeError):
            pass
    data = request_json(
        {
            "action": "parse",
            "page": title,
            "prop": "text|wikitext|revid|displaytitle",
            "redirects": 1,
        }
    )
    if "error" in data:
        error = data["error"]
        if isinstance(error, dict) and error.get("code") in PUBLICLY_UNAVAILABLE_CODES:
            raise PublicPageUnavailable(title, error)
        raise RuntimeError(f"{title}: {error}")
    parsed = data["parse"]
    page = {
        "requested_title": title,
        "title": parsed["title"],
        "pageid": parsed["pageid"],
        "revid": parsed["revid"],
        "displaytitle": parsed.get("displaytitle"),
        "html": parsed["text"],
        "wikitext": parsed.get("wikitext", ""),
    }
    DEFAULT_RAW_CACHE.mkdir(parents=True, exist_ok=True)
    temporary = cache.with_name(f".{cache.name}.stage-{os.getpid()}-{time.time_ns()}")
    temporary.write_text(
        json.dumps(page, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    os.replace(temporary, cache)
    return page


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def build_markdown(
    page: dict[str, Any],
    retrieved: str,
    title_paths: dict[str, str],
) -> tuple[bytes, dict[str, Any]]:
    prepared, source_text, links, anchors = prepare_page_html(page, title_paths)
    source_representation = "expanded-html-visible-text"
    if source_text.strip():
        try:
            converted = run_html2md(prepared)
        except (RuntimeError, ValueError) as exc:
            raise type(exc)(f"{page['title']}: {exc}") from exc
    else:
        # Some main-namespace titles redirect to category pages whose expanded
        # HTML contains comments only. Preserve their exact revision-bound
        # official wikitext instead of silently omitting the page.
        source_text = str(page.get("wikitext", ""))
        longest_backtick_run = max(
            (len(match.group(0)) for match in re.finditer(r"`+", source_text)),
            default=0,
        )
        fence = "`" * max(3, longest_backtick_run + 1)
        converted = (
            "The official expanded HTML has no visible body text. "
            "Its exact revision-bound wikitext follows.\n\n"
            f"{fence}mediawiki\n{source_text}\n{fence}\n"
        )
        source_representation = "exact-wikitext-empty-expanded-html-fallback"
    content = (
        f"# {page['title']}\n\n"
        f"- Official URL: {page_url(page['title'])}\n"
        f"- Page ID: {page['pageid']}\n"
        f"- Revision ID: {page['revid']}\n"
        f"- Retrieved UTC: {retrieved}\n"
        f"- Source: official VASP Wiki expanded HTML via MediaWiki API\n"
        f"- License: `GFDL-1.2-only`\n"
        f"- Converter: `helloworld-Co/html2md` at `{HTML2MD_COMMIT}`\n\n"
        "---\n\n"
        f"{converted}"
    )
    quality = conversion_quality(source_text, content, page["title"])
    quality["source_representation"] = source_representation
    quality["internal_links"] = links
    quality["anchors"] = anchors
    return content.encode("utf-8"), quality


def collect_titles(scope: str) -> tuple[dict[str, list[str]], list[str]]:
    if scope == "core":
        return {}, sorted(set(CORE_PAGES))
    if scope == "all-main-namespace":
        return {}, all_main_namespace_titles()
    if scope != "bounded-categories":
        raise ValueError(
            "scope must be core, bounded-categories, or all-main-namespace"
        )
    category_map = {category: category_titles(category) for category in CATEGORIES}
    titles = sorted(set(CORE_PAGES).union(*(set(items) for items in category_map.values())))
    return category_map, titles


def write_snapshot(
    root: Path,
    retrieved: str,
    category_map: dict[str, list[str]],
    titles: list[str],
    pages: list[dict[str, Any]],
    unavailable_titles: list[dict[str, str]],
    scope: str,
    workers: int,
) -> None:
    official_dir = root / "references" / "official-wiki"
    aliases_by_pageid: dict[int, set[str]] = {}
    unique_pages: dict[int, dict[str, Any]] = {}
    for page in pages:
        pageid = page["pageid"]
        aliases_by_pageid.setdefault(pageid, set()).add(page["requested_title"])
        aliases_by_pageid[pageid].add(page["title"])
        previous = unique_pages.get(pageid)
        if previous is not None:
            if previous["revid"] == page["revid"]:
                if previous["wikitext"] != page["wikitext"]:
                    raise ValueError(
                        f"inconsistent source for VASP Wiki page ID/revision "
                        f"{pageid}/{page['revid']}"
                    )
                # MediaWiki can expand one immutable revision into HTML with
                # request-local IDs. Choose deterministically while retaining
                # the exact revision-bound wikitext in the raw record.
                if previous["html"] <= page["html"]:
                    continue
            if previous["revid"] > page["revid"]:
                continue
        unique_pages[pageid] = page
    title_paths: dict[str, str] = {}
    folded_paths: dict[str, set[str]] = {}
    for pageid, page in unique_pages.items():
        stem = f"page-{pageid}-{slugify(page['title'])}.md"
        for alias in aliases_by_pageid[pageid]:
            exact_key = f"exact:{alias}"
            previous = title_paths.get(exact_key)
            if previous is not None and previous != stem:
                raise ValueError(f"ambiguous exact VASP Wiki title alias: {alias}")
            title_paths[exact_key] = stem
            folded_paths.setdefault(alias.casefold(), set()).add(stem)
    for folded, paths in folded_paths.items():
        if len(paths) == 1:
            title_paths[f"fold:{folded}"] = next(iter(paths))
    def render_entry(page: dict[str, Any]) -> dict[str, Any]:
        stem = f"page-{page['pageid']}-{slugify(page['title'])}"
        markdown_rel = Path("references") / "official-wiki" / f"{stem}.md"
        raw_rel = Path("references") / "official-wiki" / "raw" / f"{stem}.json"
        markdown, quality = build_markdown(page, retrieved, title_paths)
        raw = json.dumps(page, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
        wikitext = str(page.get("wikitext", "")).encode("utf-8")
        write_bytes(root / markdown_rel, markdown)
        write_bytes(root / raw_rel, raw)
        return {
            "title": page["title"],
            "pageid": page["pageid"],
            "revid": page["revid"],
            "aliases": sorted(aliases_by_pageid[page["pageid"]]),
            "url": page_url(page["title"]),
            "markdown_path": str(markdown_rel),
            "markdown_sha256": sha256_bytes(markdown),
            "raw_path": str(raw_rel),
            "raw_sha256": sha256_bytes(raw),
            "raw_bytes": len(raw),
            "wikitext_sha256": sha256_bytes(wikitext),
            "wikitext_bytes": len(wikitext),
            "conversion_quality": quality,
        }

    with ThreadPoolExecutor(max_workers=min(workers, 8)) as executor:
        entries = list(
            executor.map(
                render_entry,
                sorted(unique_pages.values(), key=lambda item: item["title"].lower()),
            )
        )
    entries.sort(key=lambda item: item["title"].casefold())
    entries_by_name = {
        Path(entry["markdown_path"]).name: entry for entry in entries
    }
    compatibility_aliases: dict[str, set[str]] = {}
    for source_entry in entries:
        for link in source_entry["conversion_quality"]["internal_links"]:
            fragment = link.get("fragment")
            target_name = link.get("target_markdown_path")
            target_entry = entries_by_name.get(target_name)
            if (
                not isinstance(fragment, str)
                or not fragment
                or target_entry is None
                or fragment
                in target_entry["conversion_quality"].get("anchors", [])
            ):
                continue
            compatibility_aliases.setdefault(target_name, set()).add(fragment)
    for target_name, aliases in sorted(compatibility_aliases.items()):
        target_entry = entries_by_name[target_name]
        markdown_path = root / target_entry["markdown_path"]
        markdown = markdown_path.read_text(encoding="utf-8")
        alias_block = "\n".join(
            f'<a id="{html.escape(alias, quote=True)}"></a>'
            for alias in sorted(aliases)
        )
        markdown = markdown.rstrip() + "\n\n" + alias_block + "\n"
        markdown_path.write_text(markdown, encoding="utf-8", newline="\n")
        markdown_raw = markdown.encode("utf-8")
        target_entry["markdown_sha256"] = sha256_bytes(markdown_raw)
        quality = target_entry["conversion_quality"]
        quality["anchors"] = sorted(set(quality["anchors"]).union(aliases))
        quality["compatibility_anchor_aliases"] = sorted(aliases)
        quality["max_line_chars"] = max(
            (len(line) for line in markdown.splitlines()),
            default=0,
        )

    manifest = {
        "official_root": OFFICIAL_ROOT,
        "api_url": API_URL,
        "retrieved_utc": retrieved,
        "scope": scope,
        "official_fragment_compatibility_alias_count": sum(
            len(aliases) for aliases in compatibility_aliases.values()
        ),
        "upstream_universe": "mediawiki-main-namespace",
        "upstream_universe_complete": scope == "all-main-namespace",
        "public_body_complete": scope == "all-main-namespace",
        "requested_title_count": len(titles),
        "resolved_requested_title_count": len(titles) - len(unavailable_titles),
        "unavailable_title_count": len(unavailable_titles),
        "unavailable_titles": unavailable_titles,
        "categories": category_map,
        "core_pages": list(CORE_PAGES),
        "page_count": len(entries),
        "internal_link_count": sum(
            len(entry["conversion_quality"]["internal_links"])
            for entry in entries
        ),
        "html2md_identity": html2md_identity(),
        "pages": entries,
    }
    write_bytes(
        official_dir / "manifest.json",
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n",
    )

    categories_by_title = {title: [] for title in titles}
    for category, members in category_map.items():
        for title in members:
            categories_by_title.setdefault(title, []).append(category)
    lines = [
        "# VASP official Wiki mirror index",
        "",
        f"- Official root: {OFFICIAL_ROOT}",
        f"- Retrieved UTC: {retrieved}",
        f"- Mirrored pages: {len(entries)}",
        f"- Publicly unavailable enumerated titles: {len(unavailable_titles)}",
        f"- Scope: {scope}",
        (
            f"- Categories: {', '.join(CATEGORIES)}"
            if category_map
            else "- Categories: none; main-namespace inventory or curated core pages"
        ),
        "- Raw official API snapshots: `references/official-wiki/raw/`",
        "- Manifest: `references/official-wiki/manifest.json`",
        "",
        "Use the matching page below, then recheck its official URL for version-sensitive claims.",
        "",
        "## Pages",
        "",
    ]
    for entry in entries:
        categories = ", ".join(categories_by_title.get(entry["title"], [])) or "curated core"
        relative = Path(entry["markdown_path"]).relative_to("references")
        lines.append(f"- [{entry['title']}]({relative.as_posix()}) — {categories}; revision {entry['revid']}")
    if unavailable_titles:
        lines.extend(["", "## Enumerated titles without a public body", ""])
        for record in unavailable_titles:
            lines.append(
                f"- `{record['title']}` — `{record['code']}`: {record['info']}"
            )
    write_bytes(root / "references" / "official-wiki-index.md", ("\n".join(lines) + "\n").encode("utf-8"))


def install_snapshot(root: Path, stage_root: Path) -> None:
    target_references = root / "references"
    target_references.mkdir(parents=True, exist_ok=True)
    target_official = target_references / "official-wiki"
    target_index = target_references / "official-wiki-index.md"
    staged_official = stage_root / "references" / "official-wiki"
    staged_index = stage_root / "references" / "official-wiki-index.md"
    if not staged_official.is_dir() or not staged_index.is_file():
        raise ValueError("staged VASP Wiki snapshot is incomplete")
    previous_official = stage_root / "previous-official-wiki"
    if target_official.exists():
        target_official.replace(previous_official)
    try:
        staged_official.replace(target_official)
        write_bytes(target_index, staged_index.read_bytes())
    except Exception:
        if target_official.exists():
            shutil.rmtree(target_official)
        if previous_official.exists():
            previous_official.replace(target_official)
        raise


def refresh(root: Path, workers: int, scope: str) -> int:
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    retrieved = utc_now()
    category_map, titles = collect_titles(scope)
    pages: list[dict[str, Any]] = []
    unavailable_titles: list[dict[str, str]] = []
    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch_page, title): title for title in titles}
        for future in as_completed(futures):
            title = futures[future]
            try:
                pages.append(future.result())
            except PublicPageUnavailable as exc:
                unavailable_titles.append(
                    {"title": exc.title, "code": exc.code, "info": exc.info}
                )
            except Exception as exc:  # network/API errors must be reported together
                failures.append(f"{title}: {exc}")
    if failures:
        for item in failures:
            print(item, file=sys.stderr)
        print(f"Refresh aborted: {len(failures)} page(s) failed", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix=".vasp-wiki-refresh-", dir=root) as directory:
        stage_root = Path(directory)
        write_snapshot(
            stage_root,
            retrieved,
            category_map,
            titles,
            pages,
            sorted(unavailable_titles, key=lambda item: item["title"].casefold()),
            scope,
            workers,
        )
        if check(stage_root) != 0:
            print("Refresh aborted: staged snapshot failed validation", file=sys.stderr)
            return 3
        install_snapshot(root, stage_root)
    print(
        f"Resolved {len(titles)} official titles into "
        f"{len({page['pageid'] for page in pages})} VASP Wiki pages; "
        f"{len(unavailable_titles)} enumerated title(s) have no public body at {retrieved}"
    )
    return 0


def check(root: Path) -> int:
    manifest_path = root / "references" / "official-wiki" / "manifest.json"
    if not manifest_path.is_file():
        print(f"Missing manifest: {manifest_path}", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    if manifest.get("official_root") != OFFICIAL_ROOT:
        failures.append("official_root mismatch")
    pages = manifest.get("pages", [])
    if manifest.get("page_count") != len(pages):
        failures.append("page_count mismatch")
    if manifest.get("scope") == "all-main-namespace":
        if manifest.get("upstream_universe_complete") is not True:
            failures.append("all-main-namespace snapshot lacks completeness evidence")
        if manifest.get("requested_title_count", 0) < len(pages):
            failures.append("requested title count is smaller than resolved pages")
        unavailable = manifest.get("unavailable_titles")
        if not isinstance(unavailable, list):
            failures.append("unavailable-title inventory is malformed")
            unavailable = []
        if manifest.get("unavailable_title_count") != len(unavailable):
            failures.append("unavailable-title count mismatch")
        if (
            manifest.get("resolved_requested_title_count", 0) + len(unavailable)
            != manifest.get("requested_title_count")
        ):
            failures.append("requested-title closure mismatch")
        if manifest.get("public_body_complete") is not True:
            failures.append("public body closure is not complete")
        for record in unavailable:
            if (
                not isinstance(record, dict)
                or record.get("code") not in PUBLICLY_UNAVAILABLE_CODES
                or not isinstance(record.get("title"), str)
                or not isinstance(record.get("info"), str)
            ):
                failures.append("invalid publicly unavailable title record")
    by_local_path = {
        Path(entry["markdown_path"]).name: entry
        for entry in pages
        if isinstance(entry, dict) and isinstance(entry.get("markdown_path"), str)
    }
    for entry in pages:
        for path_key, hash_key in (("markdown_path", "markdown_sha256"), ("raw_path", "raw_sha256")):
            path = root / entry[path_key]
            if not path.is_file():
                failures.append(f"missing {entry[path_key]}")
            elif sha256_bytes(path.read_bytes()) != entry[hash_key]:
                failures.append(f"hash mismatch {entry[path_key]}")
        raw_path = root / entry["raw_path"]
        if raw_path.is_file() and entry.get("raw_bytes") != raw_path.stat().st_size:
            failures.append(f"byte-count mismatch {entry['raw_path']}")
        if raw_path.is_file():
            try:
                raw_record = json.loads(raw_path.read_text(encoding="utf-8"))
                wikitext = str(raw_record.get("wikitext", "")).encode("utf-8")
            except (OSError, UnicodeError, json.JSONDecodeError):
                failures.append(f"invalid raw JSON {entry['raw_path']}")
            else:
                if (
                    entry.get("wikitext_sha256") != sha256_bytes(wikitext)
                    or entry.get("wikitext_bytes") != len(wikitext)
                ):
                    failures.append(f"wikitext identity mismatch {entry['raw_path']}")
        markdown_path = root / entry["markdown_path"]
        if markdown_path.is_file():
            try:
                markdown = markdown_path.read_text(encoding="utf-8", errors="strict")
            except (OSError, UnicodeError):
                failures.append(f"invalid UTF-8 {entry['markdown_path']}")
            else:
                if "\ufffd" in markdown or "\x00" in markdown:
                    failures.append(f"invalid display characters {entry['markdown_path']}")
        quality = entry.get("conversion_quality")
        if (
            not isinstance(quality, dict)
            or quality.get("status") != "pass"
            or quality.get("token_sequence_preserved") is not True
            or quality.get("non_ascii_characters_preserved") is not True
        ):
            failures.append(f"conversion quality failure {entry.get('title')}")
            continue
        for link in quality.get("internal_links", []):
            target_path = link.get("target_markdown_path")
            fragment = link.get("fragment")
            target = by_local_path.get(target_path)
            if not isinstance(target, dict):
                failures.append(
                    f"unresolved internal link {entry.get('title')} -> {target_path}"
                )
                continue
            if fragment and fragment not in target.get("conversion_quality", {}).get("anchors", []):
                failures.append(
                    f"unresolved internal anchor {entry.get('title')} -> "
                    f"{target.get('title')}#{fragment}"
                )
    expected_markdown = {root / entry["markdown_path"] for entry in pages}
    expected_raw = {root / entry["raw_path"] for entry in pages}
    official_dir = root / "references" / "official-wiki"
    actual_markdown = set(official_dir.glob("page-*.md")) if official_dir.is_dir() else set()
    raw_dir = official_dir / "raw"
    actual_raw = set(raw_dir.glob("page-*.json")) if raw_dir.is_dir() else set()
    for path in sorted(actual_markdown - expected_markdown):
        failures.append(f"stale unmanifested page {path.relative_to(root)}")
    for path in sorted(actual_raw - expected_raw):
        failures.append(f"stale unmanifested raw page {path.relative_to(root)}")
    index = root / "references" / "official-wiki-index.md"
    if not index.is_file():
        failures.append("missing references/official-wiki-index.md")
    if failures:
        for item in failures:
            print(item, file=sys.stderr)
        return 1
    print(
        f"Integrity-checked {len(pages)} pages in scope "
        f"{manifest.get('scope')!r}; "
        f"upstream_universe_complete={manifest.get('upstream_universe_complete')!r}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refresh", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument(
        "--check-if-present",
        action="store_true",
        help="strictly check an installed external mirror, or skip when it is absent",
    )
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument(
        "--scope",
        choices=("core", "bounded-categories", "all-main-namespace"),
        default="all-main-namespace",
        help=(
            "all-main-namespace is the release gate; smaller scopes are for diagnostics"
        ),
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_CACHE_ROOT)
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 16:
        parser.error("--workers must be between 1 and 16")
    if args.check_if_present and not args.root.exists():
        print(
            json.dumps(
                {
                    "status": "skipped",
                    "reason": "external VASP Wiki provider mirror is not installed",
                },
                sort_keys=True,
            )
        )
        return 0
    return refresh(args.root, args.workers, args.scope) if args.refresh else check(args.root)


if __name__ == "__main__":
    raise SystemExit(main())
