#!/usr/bin/env python3
"""Mirror searchable official VASP Wiki pages with provenance and integrity checks."""

from __future__ import annotations

import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
import re
import shutil
import ssl
import sys
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


def fetch_page(title: str) -> dict[str, Any]:
    data = request_json(
        {
            "action": "parse",
            "page": title,
            "prop": "text|wikitext|revid|displaytitle",
            "redirects": 1,
        }
    )
    if "error" in data:
        raise RuntimeError(f"{title}: {data['error']}")
    parsed = data["parse"]
    return {
        "requested_title": title,
        "title": parsed["title"],
        "pageid": parsed["pageid"],
        "revid": parsed["revid"],
        "displaytitle": parsed.get("displaytitle"),
        "html": parsed["text"],
        "wikitext": parsed.get("wikitext", ""),
    }


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def build_markdown(page: dict[str, Any], retrieved: str) -> bytes:
    searchable = html_to_text(page["html"])
    content = (
        f"# {page['title']}\n\n"
        f"- Official URL: {page_url(page['title'])}\n"
        f"- Page ID: {page['pageid']}\n"
        f"- Revision ID: {page['revid']}\n"
        f"- Retrieved UTC: {retrieved}\n"
        f"- Source: official VASP Wiki expanded page text\n\n"
        f"## Searchable official text\n\n{searchable}"
    )
    return content.encode("utf-8")


def collect_titles(scope: str) -> tuple[dict[str, list[str]], list[str]]:
    if scope == "core":
        return {}, sorted(set(CORE_PAGES))
    category_map = {category: category_titles(category) for category in CATEGORIES}
    titles = sorted(set(CORE_PAGES).union(*(set(items) for items in category_map.values())))
    return category_map, titles


def write_snapshot(
    root: Path,
    retrieved: str,
    category_map: dict[str, list[str]],
    titles: list[str],
    pages: list[dict[str, Any]],
    scope: str,
) -> None:
    official_dir = root / "references" / "official-wiki"
    entries: list[dict[str, Any]] = []
    for page in sorted(pages, key=lambda item: item["title"].lower()):
        stem = f"page-{page['pageid']}-{slugify(page['title'])}"
        markdown_rel = Path("references") / "official-wiki" / f"{stem}.md"
        raw_rel = Path("references") / "official-wiki" / "raw" / f"{stem}.json"
        markdown = build_markdown(page, retrieved)
        raw = json.dumps(page, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
        write_bytes(root / markdown_rel, markdown)
        write_bytes(root / raw_rel, raw)
        entries.append(
            {
                "title": page["title"],
                "pageid": page["pageid"],
                "revid": page["revid"],
                "url": page_url(page["title"]),
                "markdown_path": str(markdown_rel),
                "markdown_sha256": sha256_bytes(markdown),
                "raw_path": str(raw_rel),
                "raw_sha256": sha256_bytes(raw),
            }
        )

    manifest = {
        "official_root": OFFICIAL_ROOT,
        "api_url": API_URL,
        "retrieved_utc": retrieved,
        "scope": scope,
        "categories": category_map,
        "core_pages": list(CORE_PAGES),
        "page_count": len(entries),
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
        f"- Scope: {scope}",
        f"- Categories: {', '.join(CATEGORIES) if category_map else 'none; curated core pages'}",
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
    retrieved = utc_now()
    category_map, titles = collect_titles(scope)
    pages: list[dict[str, Any]] = []
    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch_page, title): title for title in titles}
        for future in as_completed(futures):
            title = futures[future]
            try:
                pages.append(future.result())
            except Exception as exc:  # network/API errors must be reported together
                failures.append(f"{title}: {exc}")
    if failures:
        for item in failures:
            print(item, file=sys.stderr)
        print(f"Refresh aborted: {len(failures)} page(s) failed", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix=".vasp-wiki-refresh-", dir=root) as directory:
        stage_root = Path(directory)
        write_snapshot(stage_root, retrieved, category_map, titles, pages, scope)
        if check(stage_root) != 0:
            print("Refresh aborted: staged snapshot failed validation", file=sys.stderr)
            return 3
        install_snapshot(root, stage_root)
    print(f"Mirrored {len(pages)} official VASP Wiki pages retrieved at {retrieved}")
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
    for entry in pages:
        for path_key, hash_key in (("markdown_path", "markdown_sha256"), ("raw_path", "raw_sha256")):
            path = root / entry[path_key]
            if not path.is_file():
                failures.append(f"missing {entry[path_key]}")
            elif sha256_bytes(path.read_bytes()) != entry[hash_key]:
                failures.append(f"hash mismatch {entry[path_key]}")
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
    print(f"Verified {len(pages)} mirrored official VASP Wiki pages")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refresh", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--scope", choices=("core", "full"), default="core")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 16:
        parser.error("--workers must be between 1 and 16")
    return refresh(args.root, args.workers, args.scope) if args.refresh else check(args.root)


if __name__ == "__main__":
    raise SystemExit(main())
