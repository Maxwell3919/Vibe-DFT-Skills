#!/usr/bin/env python3
"""Mirror and split official Quantum ESPRESSO manuals from quantum-espresso.org."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


BASE_URL = "https://www.quantum-espresso.org/Doc"
GUIDES = {
    "build": "user_guide",
    "pw": "pw_user_guide",
    "ph": "ph_user_guide",
    "pp": "pp_user_guide",
    "neb": "neb_user_guide",
}
PDF_DIRECTORY = "user_guide_PDF"
USER_AGENT = "qe-official-params-skill/1.0 (+official manual mirror)"
SECTION_RE = re.compile(r"^\s*(NAMELIST|CARD):\s*(.+?)\s*$", flags=re.M | re.I)
VARIABLE_RE = re.compile(r"^\s*Variable:\s*(.+?)\s*$", flags=re.M | re.I)
ITEM_MARKER_RE = re.compile(r"\[\[(QE_OFFICIAL_ITEM_\d{4})\]\]")
SECTION_MARKER_RE = re.compile(r"\[\[(QE_OFFICIAL_SECTION_\d{4})\]\]")

@dataclass
class Fetched:
    url: str
    body: bytes
    content_type: str
    last_modified: str | None
    retrieved_utc: str
    from_cache: bool = False

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.body).hexdigest()


def fetch(url: str, retries: int = 3) -> Fetched:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with tempfile.TemporaryDirectory() as tempdir:
                header_path = Path(tempdir) / "headers.txt"
                body_path = Path(tempdir) / "body.bin"
                completed = subprocess.run(
                    [
                        "curl",
                        "-L",
                        "--fail",
                        "--retry",
                        "3",
                        "--retry-all-errors",
                        "--max-time",
                        "45",
                        "-sS",
                        "-A",
                        USER_AGENT,
                        "-D",
                        str(header_path),
                        "-o",
                        str(body_path),
                        "-w",
                        "%{url_effective}\n%{content_type}\n",
                        url,
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                output_lines = completed.stdout.splitlines()
                effective_url = output_lines[0] if output_lines else url
                content_type = output_lines[1].split(";", 1)[0] if len(output_lines) > 1 else "application/octet-stream"
                header_text = header_path.read_text(encoding="iso-8859-1", errors="replace")
                last_modified_matches = re.findall(r"(?im)^Last-Modified:\s*(.+?)\s*$", header_text)
                return Fetched(
                    url=effective_url,
                    body=body_path.read_bytes(),
                    content_type=content_type,
                    last_modified=last_modified_matches[-1] if last_modified_matches else None,
                    retrieved_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                )
        except Exception as exc:  # pragma: no cover - network retry path
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def slug(value: str) -> str:
    value = html.unescape(value).strip().lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "section"


def safe_fence(text: str) -> str:
    fence = "```"
    while fence in text:
        fence += "`"
    return fence


def official_markdown(
    title: str,
    source_url: str,
    retrieved: str,
    source_sha256: str,
    official_text: str,
    last_modified: str | None = None,
    content_status: str = "official text split without substantive additions",
) -> str:
    rendered_text = official_text.rstrip("\n")
    fence = safe_fence(rendered_text)
    text_sha256 = hashlib.sha256(rendered_text.encode("utf-8")).hexdigest()
    lines = [
        f"# {title}",
        "",
        f"- Official source: {source_url}",
        f"- Retrieved: {retrieved}",
        f"- Official source SHA-256: `{source_sha256}`",
        f"- Extracted text SHA-256: `{text_sha256}`",
    ]
    if last_modified:
        lines.append(f"- Official Last-Modified: {last_modified}")
    lines.extend(
        [
            f"- Content status: {content_status}; wrapper metadata added by the mirror script.",
            "",
            f"{fence}text",
            rendered_text,
            fence,
            "",
        ]
    )
    return "\n".join(lines)


def split_input_manual(
    text: str,
    item_labels: dict[str, str] | None = None,
    section_labels: dict[str, tuple[str, str]] | None = None,
) -> list[tuple[str, str, str]]:
    top_sections: list[tuple[str, str, str]] = []
    seen: dict[str, int] = {}
    if section_labels:
        matches = list(SECTION_MARKER_RE.finditer(text))
        if not matches:
            raise RuntimeError("HTML input manual contained no structural section markers")
        prefix = text[: matches[0].start()]
        if prefix.strip():
            top_sections.append(("overview", "Overview and input structure", prefix))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            marker = match.group(1)
            base, title = section_labels[marker]
            seen[base] = seen.get(base, 0) + 1
            section_id = base if seen[base] == 1 else f"{base}-{seen[base]}"
            top_sections.append((section_id, title, text[match.end() : end]))
        expected_top_text = SECTION_MARKER_RE.sub("", text)
        assert "".join(body for _, _, body in top_sections) == expected_top_text
    else:
        matches = list(SECTION_RE.finditer(text))
        if not matches:
            return [("overview", "Overview", text)]
        prefix = text[: matches[0].start()]
        if prefix.strip():
            top_sections.append(("overview", "Overview and input structure", prefix))
        for index, match in enumerate(matches):
            kind = match.group(1).lower()
            label = match.group(2).strip()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            body = text[match.start() : end]
            base = f"{kind}-{slug(label)}"
            seen[base] = seen.get(base, 0) + 1
            section_id = base if seen[base] == 1 else f"{base}-{seen[base]}"
            top_sections.append((section_id, f"{kind.upper()}: {label}", body))
        assert "".join(body for _, _, body in top_sections) == text

    sections: list[tuple[str, str, str]] = []
    for section_id, section_title, body in top_sections:
        item_matches = list(ITEM_MARKER_RE.finditer(body)) if item_labels else []
        if item_matches:
            prefix = body[: item_matches[0].start()]
            if prefix:
                sections.append((f"{section_id}-overview", f"{section_title} — overview", prefix))
            item_seen: dict[str, int] = {}
            for index, match in enumerate(item_matches):
                end = item_matches[index + 1].start() if index + 1 < len(item_matches) else len(body)
                marker = match.group(1)
                label = item_labels[marker]
                item_id = slug(label)
                item_seen[item_id] = item_seen.get(item_id, 0) + 1
                suffix = "" if item_seen[item_id] == 1 else f"-{item_seen[item_id]}"
                sections.append(
                    (
                        f"{section_id}-item-{item_id}{suffix}",
                        f"{section_title} — Item: {label}",
                        body[match.end() : end],
                    )
                )
            continue
        if not section_id.startswith("namelist-"):
            sections.append((section_id, section_title, body))
            continue
        variable_matches = list(VARIABLE_RE.finditer(body))
        if not variable_matches:
            sections.append((section_id, section_title, body))
            continue
        starts: list[int] = []
        for match in variable_matches:
            line_start = body.rfind("\n", 0, match.start()) + 1
            previous_end = max(0, line_start - 1)
            previous_start = body.rfind("\n", 0, previous_end) + 1
            previous_line = body[previous_start:previous_end]
            starts.append(previous_start if re.fullmatch(r"\s*\+-{10,}\s*", previous_line) else line_start)
        prefix = body[: starts[0]]
        if prefix:
            sections.append((f"{section_id}-overview", f"{section_title} — overview", prefix))
        variable_seen: dict[str, int] = {}
        for index, (match, start) in enumerate(zip(variable_matches, starts)):
            end = starts[index + 1] if index + 1 < len(starts) else len(body)
            variable = match.group(1).strip()
            variable_id = slug(variable)
            variable_seen[variable_id] = variable_seen.get(variable_id, 0) + 1
            suffix = "" if variable_seen[variable_id] == 1 else f"-{variable_seen[variable_id]}"
            sections.append(
                (
                    f"{section_id}-variable-{variable_id}{suffix}",
                    f"{section_title} — Variable: {variable}",
                    body[start:end],
                )
            )
        assert "".join(item[2] for item in sections[-(len(variable_matches) + (1 if prefix else 0)) :]) == body
    expected_text = ITEM_MARKER_RE.sub("", text) if item_labels else text
    if section_labels:
        expected_text = SECTION_MARKER_RE.sub("", expected_text)
    assert "".join(body for _, _, body in sections) == expected_text
    return sections


def html_soup_to_text(soup) -> str:
    for image in soup.find_all("img"):
        alt = image.get("alt", "").strip()
        image.replace_with(f" {alt} " if alt else " ")
    body = soup.body or soup
    text = body.get_text("\n")
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"(?im)^(Namelist:\s*&)\s*\n\s*([A-Za-z0-9_]+)\s*$", r"\1\2", text)
    return text.strip() + "\n"


def cleaned_html_soup(source: str):
    from bs4 import BeautifulSoup, Comment

    soup = BeautifulSoup(source, "lxml")
    for node in soup(["script", "style"]):
        node.decompose()
    for comment in soup.find_all(string=lambda value: isinstance(value, Comment)):
        comment.extract()
    return soup


class GuideTextExtractor:
    """Small HTML-to-text converter that preserves headings, lists, pre blocks, and image alt text."""

    def __init__(self, source: str):
        soup = cleaned_html_soup(source)
        self.text = html_soup_to_text(soup)


class InputHtmlTextExtractor:
    """Convert an official INPUT_*.html page while retaining item boundaries."""

    def __init__(self, source: str):
        from bs4 import NavigableString

        soup = cleaned_html_soup(source)
        self.section_labels: dict[str, tuple[str, str]] = {}
        for table in soup.find_all("table"):
            row = table.find("tr", recursive=False)
            cells = row.find_all(["th", "td"], recursive=False) if row else []
            heading = cells[0].find(["h2", "h3"], recursive=False) if cells else None
            if not heading:
                continue
            heading_text = " ".join(heading.get_text(" ", strip=True).split()).replace("& ", "&")
            lowered = heading_text.lower()
            if lowered.startswith("namelist:"):
                label = heading_text.split(":", 1)[1].strip()
                base = f"namelist-{slug(label)}"
                title = f"NAMELIST: {label}"
            elif lowered.startswith("card:"):
                label = heading_text.split(":", 1)[1].strip()
                base = f"card-{slug(label)}"
                title = f"CARD: {label}"
            elif lowered == "line of input":
                base = "line-of-input"
                title = "LINE OF INPUT"
            else:
                continue
            marker = f"QE_OFFICIAL_SECTION_{len(self.section_labels):04d}"
            self.section_labels[marker] = (base, title)
            table.insert_before(NavigableString(f"\n[[{marker}]]\n"))
        self.item_labels: dict[str, str] = {}
        for table in soup.find_all("table"):
            row = table.find("tr", recursive=False)
            cells = row.find_all(["th", "td"], recursive=False) if row else []
            if len(cells) < 2 or cells[0].name != "th":
                continue
            style = cells[0].get("style", "").replace(" ", "").lower()
            if "background:#ffff99" not in style:
                continue
            label = " ".join(cells[0].get_text(" ", strip=True).split())
            marker = f"QE_OFFICIAL_ITEM_{len(self.item_labels):04d}"
            self.item_labels[marker] = label
            table.insert_before(NavigableString(f"\n[[{marker}]]\n"))
        self.text = html_soup_to_text(soup)


def parse_hrefs(source: str, pattern: str) -> list[str]:
    values = re.findall(r'href=["\']([^"\']+)["\']', source, flags=re.I)
    return sorted({html.unescape(value) for value in values if re.fullmatch(pattern, value)})


def split_release_notes(text: str) -> list[tuple[str, str, str]]:
    heading_re = re.compile(
        r"^(?P<title>(?:Incompatible changes|New|Fixed|Known problems)[^\n]*?:)\s*$",
        flags=re.M | re.I,
    )
    matches = list(heading_re.finditer(text))
    if not matches:
        return [("overview", "Release notes", text)]
    sections: list[tuple[str, str, str]] = []
    prefix = text[: matches[0].start()]
    if prefix.strip():
        sections.append(("overview", "Release notes overview", prefix))
    seen: dict[str, int] = {}
    for index, match in enumerate(matches):
        title = match.group("title").strip()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        base = slug(title)
        seen[base] = seen.get(base, 0) + 1
        suffix = "" if seen[base] == 1 else f"-{seen[base]}"
        sections.append((f"release-{base}{suffix}", title, text[match.start() : end]))
    assert "".join(body for _, _, body in sections) == text
    return sections


def extract_pdf_pages(pdf_path: Path) -> tuple[int, list[str]]:
    info = subprocess.run(["pdfinfo", str(pdf_path)], check=True, capture_output=True)
    info_text = info.stdout.decode("utf-8", errors="replace")
    page_match = re.search(r"(?m)^Pages:\s*(\d+)\s*$", info_text)
    if not page_match:
        raise RuntimeError(f"Could not determine PDF page count: {pdf_path}")
    page_count = int(page_match.group(1))
    extracted = subprocess.run(["pdftotext", "-layout", str(pdf_path), "-"], check=True, capture_output=True)
    text = extracted.stdout.decode("utf-8", errors="replace")
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    if len(pages) < page_count:
        pages.extend([""] * (page_count - len(pages)))
    if len(pages) != page_count:
        raise RuntimeError(f"PDF page extraction mismatch for {pdf_path}: {len(pages)} != {page_count}")
    return page_count, pages


def clear_generated(references: Path) -> None:
    for path in references.glob("official-input-*.md"):
        path.unlink()
    for path in references.glob("official-guide-*.md"):
        path.unlink()
    for path in references.glob("official-manual-*-index.md"):
        path.unlink()
    for path in references.glob("official-guide-*-index.md"):
        path.unlink()
    for path in references.glob("official-pdf-*.md"):
        path.unlink()
    for path in references.glob("official-release-notes-*.md"):
        path.unlink()
    for name in ["official-manual-index.md", "official-manifest.json", "official-release-notes-index.md"]:
        path = references / name
        if path.exists():
            path.unlink()


def source_cache_from_manifest(manifest: dict | None) -> dict[str, dict]:
    if not manifest:
        return {}
    if isinstance(manifest.get("source_cache"), dict):
        return dict(manifest["source_cache"])
    retrieved_utc = manifest.get("retrieved_utc")
    cache: dict[str, dict] = {}

    def add(record: dict, content_type: str) -> None:
        raw_file = record.get("raw_file")
        if not raw_file:
            return
        cache[raw_file] = {
            "url": record.get("url"),
            "content_type": content_type,
            "last_modified": record.get("last_modified"),
            "retrieved_utc": record.get("retrieved_utc") or retrieved_utc,
            "sha256": record.get("sha256") or record.get("html_sha256"),
        }

    for manual in manifest.get("input_manuals", []):
        content_type = "text/plain" if manual.get("source_format") == "txt" else "text/html"
        add(manual, content_type)
    for guide in manifest.get("user_guides", []):
        for page in guide.get("pages", []):
            add(page, "text/html")
    if manifest.get("release_notes"):
        add(manifest["release_notes"], "text/plain")
    for pdf in manifest.get("pdf_manuals", []):
        add(pdf, "application/pdf")
    return cache


def fetched_metadata(fetched: Fetched) -> dict:
    return {
        "url": fetched.url,
        "content_type": fetched.content_type,
        "last_modified": fetched.last_modified,
        "retrieved_utc": fetched.retrieved_utc,
        "sha256": fetched.sha256,
    }


def cached_fetch(
    url: str,
    raw_path: Path,
    cached_metadata: dict | None = None,
    fallback_retrieved_utc: str | None = None,
) -> Fetched:
    if raw_path.is_file() and raw_path.stat().st_size > 0:
        body = raw_path.read_bytes()
        body_hash = hashlib.sha256(body).hexdigest()
        if cached_metadata and cached_metadata.get("sha256") and cached_metadata["sha256"] != body_hash:
            raise RuntimeError(
                f"Cached source hash does not match provenance metadata: {raw_path}; run with --refresh"
            )
        retrieved_utc = (cached_metadata or {}).get("retrieved_utc") or fallback_retrieved_utc
        if not retrieved_utc:
            raise RuntimeError(f"Cached source has no retrieval provenance: {raw_path}; run with --refresh")
        return Fetched(
            url=(cached_metadata or {}).get("url") or url,
            body=body,
            content_type=(cached_metadata or {}).get("content_type") or "application/octet-stream",
            last_modified=(cached_metadata or {}).get("last_modified"),
            retrieved_utc=retrieved_utc,
            from_cache=True,
        )
    fetched = fetch(url)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(fetched.body)
    return fetched


def markdown_payload(path: Path) -> tuple[str, str, str]:
    text = path.read_text(encoding="utf-8")
    source_match = re.search(r"(?m)^- Official source SHA-256: `([0-9a-f]{64})`$", text)
    extracted_match = re.search(r"(?m)^- Extracted text SHA-256: `([0-9a-f]{64})`$", text)
    fence_match = re.search(r"(?m)^(`{3,})text$", text)
    if not source_match or not extracted_match or not fence_match:
        raise RuntimeError(f"Missing provenance metadata or text fence: {path}")
    fence = fence_match.group(1)
    payload_start = fence_match.end() + 1
    closing = re.search(rf"(?m)^{re.escape(fence)}$", text[payload_start:])
    if not closing:
        raise RuntimeError(f"Missing closing text fence: {path}")
    payload = text[payload_start : payload_start + closing.start()]
    if payload.endswith("\n"):
        payload = payload[:-1]
    return source_match.group(1), extracted_match.group(1), payload


def _build_in_place(skill_root: Path, refresh: bool = False) -> dict:
    references = skill_root / "references"
    references.mkdir(parents=True, exist_ok=True)
    previous_manifest_path = references / "official-manifest.json"
    previous_manifest = (
        json.loads(previous_manifest_path.read_text(encoding="utf-8"))
        if previous_manifest_path.is_file()
        else None
    )
    prior_cache = {} if refresh else source_cache_from_manifest(previous_manifest)
    fallback_retrieved_utc = None if refresh else (previous_manifest or {}).get("retrieved_utc")
    clear_generated(references)
    raw_root = references / "official-raw"
    if refresh and raw_root.exists():
        shutil.rmtree(raw_root)
    raw_root.mkdir(parents=True, exist_ok=True)

    generated_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    source_cache: dict[str, dict] = {}
    cache_hits = 0
    live_fetches = 0

    def fetch_source(url: str, raw_path: Path) -> Fetched:
        nonlocal cache_hits, live_fetches
        relative = str(raw_path.relative_to(references))
        fetched = cached_fetch(url, raw_path, prior_cache.get(relative), fallback_retrieved_utc)
        source_cache[relative] = fetched_metadata(fetched)
        if fetched.from_cache:
            cache_hits += 1
        else:
            live_fetches += 1
        return fetched

    manifest: dict = {
        "source_root": f"{BASE_URL}/",
        "generated_utc": generated_utc,
        "input_manuals": [],
        "user_guides": [],
    }

    directory = fetch_source(f"{BASE_URL}/", raw_root / "Doc-index.html")
    directory_html = directory.body.decode("utf-8", errors="replace")
    input_txt_names = parse_hrefs(directory_html, r"INPUT_[^/?#]+\.txt")
    input_html_names = parse_hrefs(directory_html, r"INPUT_[^/?#]+\.html")
    txt_by_base = {name.removesuffix(".txt"): name for name in input_txt_names}
    html_by_base = {name.removesuffix(".html"): name for name in input_html_names}
    manual_bases = sorted(set(txt_by_base) | set(html_by_base))
    input_sources = [(base, txt_by_base.get(base), html_by_base.get(base)) for base in manual_bases]
    if not input_sources:
        raise RuntimeError("No official INPUT_*.txt manuals found")
    print(f"DISCOVERED unique input manuals: {len(input_sources)}", flush=True)

    index_lines = ["## Input manuals", ""]

    for manual_id, txt_name, html_name in input_sources:
        source_name = txt_name or html_name
        assert source_name is not None
        source_format = "txt" if txt_name else "html"
        print(f"FETCH input {source_name}", flush=True)
        url = f"{BASE_URL}/{urllib.parse.quote(source_name)}"
        raw_path = raw_root / source_name
        fetched = fetch_source(url, raw_path)
        source_text = fetched.body.decode("utf-8", errors="replace")
        item_labels: dict[str, str] | None = None
        section_labels: dict[str, tuple[str, str]] | None = None
        if source_format == "txt":
            text = source_text.replace("\r\n", "\n")
        else:
            extracted = InputHtmlTextExtractor(source_text)
            text = extracted.text
            item_labels = extracted.item_labels
            section_labels = extracted.section_labels
        txt_is_incomplete = source_format == "txt" and (
            len(text) < 500 or ("INPUT FILE DESCRIPTION" not in text and "Program:" not in text)
        )
        if txt_is_incomplete:
            if not html_name:
                raise RuntimeError(f"Official TXT manual is incomplete and no HTML fallback exists: {txt_name}")
            print(f"  FALLBACK to complete official HTML: {html_name}", flush=True)
            source_name = html_name
            source_format = "html"
            url = f"{BASE_URL}/{urllib.parse.quote(source_name)}"
            raw_path = raw_root / source_name
            fetched = fetch_source(url, raw_path)
            source_text = fetched.body.decode("utf-8", errors="replace")
            extracted = InputHtmlTextExtractor(source_text)
            text = extracted.text
            item_labels = extracted.item_labels
            section_labels = extracted.section_labels
        manual_slug = slug(manual_id.removeprefix("INPUT_"))
        version_match = re.search(r"version:\s*([^\)\n]+)", text, flags=re.I)
        program_match = re.search(r"Program:\s*([^\n]+)", text)
        manual_version = version_match.group(1).strip() if version_match else None
        sections = split_input_manual(text, item_labels, section_labels)
        section_records = []
        manual_index_filename = f"official-manual-{manual_slug}-index.md"
        manual_index_lines = [
            f"# {manual_id} Official Manual Index",
            "",
            f"- Official source: {url}",
            f"- Program: {program_match.group(1).strip() if program_match else 'not stated'}",
            f"- Manual version: {manual_version or 'not stated'}",
            f"- Source retrieved UTC: {fetched.retrieved_utc}",
            f"- Sections: {len(sections)}",
            f"- Official format mirrored: {source_format.upper()}",
            f"- Raw: [official-raw/{source_name}](official-raw/{source_name})",
            "",
            "## Sections",
            "",
        ]
        index_lines.extend(
            [f"- [{manual_id}]({manual_index_filename}) — v{manual_version or 'unknown'}, {len(sections)} sections", ""]
        )
        for order, (section_id, section_title, section_text) in enumerate(sections):
            filename = f"official-input-{manual_slug}-{order:02d}-{section_id}.md"
            path = references / filename
            rendered_section = section_text.rstrip("\n")
            section_hash = hashlib.sha256(rendered_section.encode("utf-8")).hexdigest()
            path.write_text(
                official_markdown(
                    f"{manual_id} — {section_title}",
                    url,
                    fetched.retrieved_utc,
                    fetched.sha256,
                    section_text,
                    fetched.last_modified,
                    (
                        "official TXT text split without substantive additions"
                        if source_format == "txt"
                        else "official text extracted from official HTML without substantive additions"
                    ),
                ),
                encoding="utf-8",
            )
            manual_index_lines.append(f"- [{section_title}]({filename})")
            section_records.append(
                {
                    "order": order,
                    "id": section_id,
                    "title": section_title,
                    "file": filename,
                    "sha256": section_hash,
                    "bytes": len(rendered_section.encode("utf-8")),
                }
            )
        (references / manual_index_filename).write_text("\n".join(manual_index_lines).rstrip() + "\n", encoding="utf-8")
        manifest["input_manuals"].append(
            {
                "name": manual_id,
                "source_format": source_format,
                "program": program_match.group(1).strip() if program_match else None,
                "version": manual_version,
                "url": fetched.url,
                "last_modified": fetched.last_modified,
                "retrieved_utc": fetched.retrieved_utc,
                "sha256": fetched.sha256,
                "raw_file": str(raw_path.relative_to(references)),
                "index_file": manual_index_filename,
                "sections": section_records,
            }
        )
        print(f"DONE input {source_name}: {len(sections)} sections", flush=True)

    index_lines.extend(["## Official User Guides", ""])
    for guide_id, directory_name in GUIDES.items():
        print(f"FETCH guide {directory_name}", flush=True)
        root_url = f"{BASE_URL}/{directory_name}/"
        raw_dir = raw_root / directory_name
        raw_dir.mkdir(parents=True, exist_ok=True)
        root = fetch_source(root_url, raw_dir / "index.html")
        root_html = root.body.decode("utf-8", errors="replace")
        node_names = parse_hrefs(root_html, r"node\d+\.html")
        page_names = ["index.html", *node_names]
        guide_index_filename = f"official-guide-{guide_id}-index.md"
        guide_index_lines = [
            f"# {directory_name} Official User Guide Index",
            "",
            f"- Official source: {root_url}",
            f"- Root page retrieved UTC: {root.retrieved_utc}",
            f"- Pages: {len(page_names)}",
            "",
            "## Pages",
            "",
        ]
        guide_record = {
            "id": guide_id,
            "directory": directory_name,
            "url": root_url,
            "index_file": guide_index_filename,
            "pages": [],
        }
        index_lines.extend([f"- [{directory_name}]({guide_index_filename}) — {len(page_names)} pages", ""])
        for order, page_name in enumerate(page_names):
            print(f"  FETCH page {page_name}", flush=True)
            page_url = root_url if page_name == "index.html" else urllib.parse.urljoin(root_url, page_name)
            page = root if page_name == "index.html" else fetch_source(page_url, raw_dir / page_name)
            page_html = page.body.decode("utf-8", errors="replace")
            (raw_dir / page_name).write_text(page_html, encoding="utf-8")
            title_match = re.search(r"<TITLE>(.*?)</TITLE>", page_html, flags=re.I | re.S)
            title = html.unescape(re.sub(r"<[^>]+>", "", title_match.group(1))).strip() if title_match else page_name
            text = GuideTextExtractor(page_html).text
            filename = f"official-guide-{guide_id}-{order:02d}-{slug(title)[:80]}.md"
            rendered_text = text.rstrip("\n")
            text_hash = hashlib.sha256(rendered_text.encode("utf-8")).hexdigest()
            (references / filename).write_text(
                official_markdown(
                    title,
                    page_url,
                    page.retrieved_utc,
                    page.sha256,
                    text,
                    page.last_modified,
                    "official text extracted from official HTML without substantive additions",
                ),
                encoding="utf-8",
            )
            guide_index_lines.append(f"- [{title}]({filename})")
            guide_record["pages"].append(
                {
                    "order": order,
                    "page": page_name,
                    "title": title,
                    "url": page_url,
                    "last_modified": page.last_modified,
                    "retrieved_utc": page.retrieved_utc,
                    "html_sha256": page.sha256,
                    "text_sha256": text_hash,
                    "raw_file": str((raw_dir / page_name).relative_to(references)),
                    "file": filename,
                }
            )
        (references / guide_index_filename).write_text("\n".join(guide_index_lines).rstrip() + "\n", encoding="utf-8")
        manifest["user_guides"].append(guide_record)

    index_lines.extend(["## Official release notes", ""])
    release_url = f"{BASE_URL}/release-notes"
    release_raw = raw_root / "release-notes"
    release = fetch_source(release_url, release_raw)
    release_text = release.body.decode("utf-8", errors="replace").replace("\r\n", "\n")
    release_sections = split_release_notes(release_text)
    release_index_filename = "official-release-notes-index.md"
    release_index_lines = [
        "# Quantum ESPRESSO Official Release Notes Index",
        "",
        f"- Official source: {release_url}",
        f"- Source retrieved UTC: {release.retrieved_utc}",
        f"- Sections: {len(release_sections)}",
        "- Raw: [official-raw/release-notes](official-raw/release-notes)",
        "",
        "## Sections",
        "",
    ]
    release_record = {
        "url": release.url,
        "last_modified": release.last_modified,
        "retrieved_utc": release.retrieved_utc,
        "sha256": release.sha256,
        "raw_file": str(release_raw.relative_to(references)),
        "index_file": release_index_filename,
        "sections": [],
    }
    for order, (section_id, section_title, section_text) in enumerate(release_sections):
        filename = f"official-release-notes-{order:03d}-{section_id}.md"
        rendered_section = section_text.rstrip("\n")
        section_hash = hashlib.sha256(rendered_section.encode("utf-8")).hexdigest()
        (references / filename).write_text(
            official_markdown(
                f"Quantum ESPRESSO release notes — {section_title}",
                release_url,
                release.retrieved_utc,
                release.sha256,
                section_text,
                release.last_modified,
                "official release-note text split without substantive additions",
            ),
            encoding="utf-8",
        )
        release_index_lines.append(f"- [{section_title}]({filename})")
        release_record["sections"].append(
            {
                "order": order,
                "id": section_id,
                "title": section_title,
                "file": filename,
                "sha256": section_hash,
                "bytes": len(rendered_section.encode("utf-8")),
            }
        )
    (references / release_index_filename).write_text(
        "\n".join(release_index_lines).rstrip() + "\n", encoding="utf-8"
    )
    manifest["release_notes"] = release_record
    index_lines.extend(
        [f"- [release-notes]({release_index_filename}) — {len(release_sections)} sections", ""]
    )

    index_lines.extend(["## Official PDF manuals", ""])
    pdf_root_url = f"{BASE_URL}/{PDF_DIRECTORY}/"
    pdf_raw_dir = raw_root / PDF_DIRECTORY
    pdf_raw_dir.mkdir(parents=True, exist_ok=True)
    pdf_directory = fetch_source(pdf_root_url, pdf_raw_dir / "index.html")
    pdf_directory_html = pdf_directory.body.decode("utf-8", errors="replace")
    pdf_names = parse_hrefs(pdf_directory_html, r"[^/?#]+\.pdf")
    if not pdf_names:
        raise RuntimeError("No official PDF manuals found")
    manifest["pdf_manuals"] = []
    for pdf_name in pdf_names:
        pdf_url = urllib.parse.urljoin(pdf_root_url, pdf_name)
        pdf_raw_path = pdf_raw_dir / pdf_name
        print(f"FETCH PDF {pdf_name}", flush=True)
        pdf = fetch_source(pdf_url, pdf_raw_path)
        page_count, pages = extract_pdf_pages(pdf_raw_path)
        pdf_slug = slug(Path(pdf_name).stem)
        pdf_index_filename = f"official-pdf-{pdf_slug}-index.md"
        pdf_index_lines = [
            f"# {pdf_name} Official PDF Index",
            "",
            f"- Official source: {pdf_url}",
            f"- Source retrieved UTC: {pdf.retrieved_utc}",
            f"- Pages: {page_count}",
            f"- Raw PDF: [official-raw/{PDF_DIRECTORY}/{pdf_name}](official-raw/{PDF_DIRECTORY}/{pdf_name})",
            "- Text extraction is for search and routing; inspect the official PDF for figures, equations, and layout.",
            "",
            "## Pages",
            "",
        ]
        pdf_record = {
            "name": pdf_name,
            "url": pdf.url,
            "last_modified": pdf.last_modified,
            "retrieved_utc": pdf.retrieved_utc,
            "sha256": pdf.sha256,
            "raw_file": str(pdf_raw_path.relative_to(references)),
            "index_file": pdf_index_filename,
            "page_count": page_count,
            "pages": [],
        }
        index_lines.extend([f"- [{pdf_name}]({pdf_index_filename}) — {page_count} pages", ""])
        for page_number, page_text in enumerate(pages, start=1):
            filename = f"official-pdf-{pdf_slug}-page-{page_number:03d}.md"
            rendered_page = page_text.rstrip("\n")
            text_hash = hashlib.sha256(rendered_page.encode("utf-8")).hexdigest()
            (references / filename).write_text(
                official_markdown(
                    f"{pdf_name} — page {page_number}",
                    pdf_url,
                    pdf.retrieved_utc,
                    pdf.sha256,
                    page_text,
                    pdf.last_modified,
                    "official text extracted from an official PDF page without substantive additions",
                ),
                encoding="utf-8",
            )
            pdf_index_lines.append(f"- [Page {page_number}]({filename})")
            pdf_record["pages"].append(
                {
                    "page": page_number,
                    "file": filename,
                    "text_sha256": text_hash,
                    "bytes": len(rendered_page.encode("utf-8")),
                }
            )
        (references / pdf_index_filename).write_text(
            "\n".join(pdf_index_lines).rstrip() + "\n", encoding="utf-8"
        )
        manifest["pdf_manuals"].append(pdf_record)

    for raw_path in raw_root.rglob("*"):
        if raw_path.is_file() and str(raw_path.relative_to(references)) not in source_cache:
            raw_path.unlink()
    for raw_dir in sorted((path for path in raw_root.rglob("*") if path.is_dir()), reverse=True):
        if not any(raw_dir.iterdir()):
            raw_dir.rmdir()

    retrieved_times = sorted({item["retrieved_utc"] for item in source_cache.values()})
    if not retrieved_times:
        raise RuntimeError("No official source retrieval metadata was recorded")
    retrieval_mode = "mixed" if cache_hits and live_fetches else ("cache" if cache_hits else "refresh")
    manifest.update(
        {
            "retrieved_utc": retrieved_times[-1],
            "oldest_source_retrieved_utc": retrieved_times[0],
            "latest_source_retrieved_utc": retrieved_times[-1],
            "retrieval_mode": retrieval_mode,
            "source_cache": source_cache,
        }
    )
    retrieval_summary = (
        retrieved_times[0]
        if retrieved_times[0] == retrieved_times[-1]
        else f"{retrieved_times[0]} to {retrieved_times[-1]}"
    )
    index_header = [
        "# Quantum ESPRESSO Official Manual Index",
        "",
        f"- Official root: {BASE_URL}/",
        f"- Generated UTC: {generated_utc}",
        f"- Official source retrieval UTC: {retrieval_summary}",
        f"- Retrieval mode: {retrieval_mode}",
        f"- Input manuals mirrored: {len(input_sources)}",
        "- Source rule: official quantum-espresso.org manuals only.",
        "- Raw official snapshots: `references/official-raw/`.",
        "",
    ]
    (references / "official-manual-index.md").write_text(
        "\n".join(index_header + index_lines).rstrip() + "\n", encoding="utf-8"
    )
    (references / "official-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def sync(skill_root: Path, refresh: bool = False) -> dict:
    """Build and validate a staged mirror, then replace references with rollback on failure."""
    skill_root = skill_root.resolve()
    with tempfile.TemporaryDirectory(prefix=f".{skill_root.name}-sync-", dir=skill_root.parent) as tempdir:
        staging_root = Path(tempdir) / skill_root.name
        shutil.copytree(skill_root, staging_root, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc"))
        _build_in_place(staging_root, refresh=refresh)
        check(staging_root)

        current_references = skill_root / "references"
        staged_references = staging_root / "references"
        backup_references = Path(tempdir) / "previous-references"
        if current_references.exists():
            os.replace(current_references, backup_references)
            try:
                os.replace(staged_references, current_references)
            except Exception:
                os.replace(backup_references, current_references)
                raise
        else:
            os.replace(staged_references, current_references)
    return json.loads((skill_root / "references" / "official-manifest.json").read_text(encoding="utf-8"))


def markdown_link_targets(path: Path) -> set[str]:
    return {
        target
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))
        if target.endswith(".md")
    }


def check(skill_root: Path) -> None:
    references = skill_root / "references"
    raw_root = references / "official-raw"
    manifest_path = references / "official-manifest.json"
    index_path = references / "official-manual-index.md"
    if not manifest_path.is_file() or not index_path.is_file():
        raise RuntimeError("Official manual mirror is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("source_root") != f"{BASE_URL}/":
        raise RuntimeError(f"Unexpected official source root: {manifest.get('source_root')}")
    if manifest.get("retrieval_mode") not in {"cache", "refresh", "mixed"}:
        raise RuntimeError(f"Invalid retrieval mode: {manifest.get('retrieval_mode')}")
    for key in ("generated_utc", "retrieved_utc", "oldest_source_retrieved_utc", "latest_source_retrieved_utc"):
        if not manifest.get(key):
            raise RuntimeError(f"Missing provenance timestamp: {key}")
    if not manifest.get("release_notes"):
        raise RuntimeError("Official release notes are missing")

    missing: list[str] = []
    mismatched: list[str] = []
    generated_files: set[str] = set()
    source_cache = manifest.get("source_cache", {})
    if not source_cache:
        mismatched.append("source cache provenance is missing")

    for raw_file, metadata in source_cache.items():
        raw_path = references / raw_file
        if not raw_path.is_file():
            missing.append(raw_file)
            continue
        raw_hash = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        if raw_hash != metadata.get("sha256"):
            mismatched.append(f"source cache hash: {raw_file}")
        if not metadata.get("retrieved_utc"):
            mismatched.append(f"source cache retrieval time: {raw_file}")
        if not str(metadata.get("url", "")).startswith(f"{BASE_URL}/"):
            mismatched.append(f"non-official source cache URL: {raw_file}")

    actual_raw_files = {
        str(path.relative_to(references))
        for path in raw_root.rglob("*")
        if path.is_file() and path.name != ".DS_Store"
    }
    if actual_raw_files != set(source_cache):
        mismatched.append(
            f"raw source set differs; stale={sorted(actual_raw_files - set(source_cache))}, "
            f"absent={sorted(set(source_cache) - actual_raw_files)}"
        )

    directory_html = (raw_root / "Doc-index.html").read_text(encoding="utf-8", errors="replace")
    discovered_names = {
        name.rsplit(".", 1)[0]
        for name in parse_hrefs(directory_html, r"INPUT_[^/?#]+\.(?:txt|html)")
    }
    manual_names = [item["name"] for item in manifest.get("input_manuals", [])]
    if len(manual_names) != len(set(manual_names)):
        mismatched.append("duplicate input manual names")
    if set(manual_names) != discovered_names:
        mismatched.append(
            f"input discovery differs; missing={sorted(discovered_names - set(manual_names))}, "
            f"unexpected={sorted(set(manual_names) - discovered_names)}"
        )

    expected_top_indexes: set[str] = set()

    def check_source_record(record: dict, hash_key: str) -> None:
        metadata = source_cache.get(record.get("raw_file"), {})
        if record.get(hash_key) != metadata.get("sha256"):
            mismatched.append(f"record/source hash: {record.get('raw_file')}")
        if record.get("retrieved_utc") != metadata.get("retrieved_utc"):
            mismatched.append(f"record/source retrieval time: {record.get('raw_file')}")
        if record.get("last_modified") != metadata.get("last_modified"):
            mismatched.append(f"record/source Last-Modified: {record.get('raw_file')}")

    for manual in manifest.get("input_manuals", []):
        check_source_record(manual, "sha256")
        raw_path = references / manual["raw_file"]
        source_text = raw_path.read_text(encoding="utf-8", errors="replace")
        if manual["source_format"] == "html":
            extracted = InputHtmlTextExtractor(source_text)
            text_value = extracted.text
            expected_sections = split_input_manual(text_value, extracted.item_labels, extracted.section_labels)
        else:
            text_value = source_text.replace("\r\n", "\n")
            expected_sections = split_input_manual(text_value)
        actual_sections = manual.get("sections", [])
        if len(expected_sections) != len(actual_sections):
            mismatched.append(f"input section count: {manual['name']}")
        for expected, section in zip(expected_sections, actual_sections):
            section_id, section_title, section_text = expected
            rendered = section_text.rstrip("\n")
            expected_hash = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
            if (section["id"], section["title"], section["sha256"], section["bytes"]) != (
                section_id,
                section_title,
                expected_hash,
                len(rendered.encode("utf-8")),
            ):
                mismatched.append(f"input split metadata: {section['file']}")
            section_path = references / section["file"]
            generated_files.add(section["file"])
            if not section_path.is_file():
                missing.append(section["file"])
                continue
            source_hash, extracted_hash, payload = markdown_payload(section_path)
            if source_hash != manual["sha256"] or extracted_hash != expected_hash or payload != rendered:
                mismatched.append(f"input generated payload: {section['file']}")
            if "[[QE_OFFICIAL_" in payload:
                mismatched.append(f"internal marker leaked: {section['file']}")
        manual_index = references / manual["index_file"]
        expected_top_indexes.add(manual["index_file"])
        if not manual_index.is_file():
            missing.append(manual["index_file"])
        elif markdown_link_targets(manual_index) != {item["file"] for item in actual_sections}:
            mismatched.append(f"manual index links: {manual['index_file']}")

    guide_ids = {item["id"] for item in manifest.get("user_guides", [])}
    if guide_ids != set(GUIDES):
        mismatched.append(f"guide scope differs: {sorted(guide_ids)}")
    for guide in manifest.get("user_guides", []):
        expected_top_indexes.add(guide["index_file"])
        root_raw = raw_root / guide["directory"] / "index.html"
        expected_pages = ["index.html", *parse_hrefs(root_raw.read_text(encoding="utf-8"), r"node\d+\.html")]
        actual_pages = [item["page"] for item in guide.get("pages", [])]
        if actual_pages != expected_pages:
            mismatched.append(f"guide page discovery: {guide['directory']}")
        for page in guide.get("pages", []):
            check_source_record(page, "html_sha256")
            raw_path = references / page["raw_file"]
            page_path = references / page["file"]
            generated_files.add(page["file"])
            if not raw_path.is_file() or not page_path.is_file():
                missing.append(page["file"])
                continue
            expected_text = GuideTextExtractor(raw_path.read_text(encoding="utf-8", errors="replace")).text.rstrip("\n")
            expected_hash = hashlib.sha256(expected_text.encode("utf-8")).hexdigest()
            source_hash, extracted_hash, payload = markdown_payload(page_path)
            if (
                source_hash != page["html_sha256"]
                or extracted_hash != expected_hash
                or page["text_sha256"] != expected_hash
                or payload != expected_text
            ):
                mismatched.append(f"guide generated payload: {page['file']}")
        guide_index = references / guide["index_file"]
        if not guide_index.is_file():
            missing.append(guide["index_file"])
        elif markdown_link_targets(guide_index) != {item["file"] for item in guide.get("pages", [])}:
            mismatched.append(f"guide index links: {guide['index_file']}")

    release = manifest["release_notes"]
    check_source_record(release, "sha256")
    expected_top_indexes.add(release["index_file"])
    release_text = (references / release["raw_file"]).read_text(encoding="utf-8", errors="replace").replace(
        "\r\n", "\n"
    )
    expected_release_sections = split_release_notes(release_text)
    if len(expected_release_sections) != len(release.get("sections", [])):
        mismatched.append("release-note section count")
    for expected, section in zip(expected_release_sections, release.get("sections", [])):
        section_id, section_title, section_text = expected
        rendered = section_text.rstrip("\n")
        expected_hash = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        section_path = references / section["file"]
        generated_files.add(section["file"])
        if not section_path.is_file():
            missing.append(section["file"])
            continue
        source_hash, extracted_hash, payload = markdown_payload(section_path)
        if (
            (section["id"], section["title"], section["sha256"], section["bytes"])
            != (section_id, section_title, expected_hash, len(rendered.encode("utf-8")))
            or source_hash != release["sha256"]
            or extracted_hash != expected_hash
            or payload != rendered
        ):
            mismatched.append(f"release-note generated payload: {section['file']}")
    release_index = references / release["index_file"]
    if not release_index.is_file():
        missing.append(release["index_file"])
    elif markdown_link_targets(release_index) != {item["file"] for item in release.get("sections", [])}:
        mismatched.append(f"release-note index links: {release['index_file']}")

    pdf_directory_html = (raw_root / PDF_DIRECTORY / "index.html").read_text(encoding="utf-8", errors="replace")
    discovered_pdfs = set(parse_hrefs(pdf_directory_html, r"[^/?#]+\.pdf"))
    pdf_names = {item["name"] for item in manifest.get("pdf_manuals", [])}
    if pdf_names != discovered_pdfs:
        mismatched.append(
            f"PDF discovery differs; missing={sorted(discovered_pdfs - pdf_names)}, "
            f"unexpected={sorted(pdf_names - discovered_pdfs)}"
        )
    for pdf in manifest.get("pdf_manuals", []):
        check_source_record(pdf, "sha256")
        expected_top_indexes.add(pdf["index_file"])
        pdf_raw = references / pdf["raw_file"]
        page_count, pages = extract_pdf_pages(pdf_raw)
        if page_count != pdf["page_count"] or len(pdf.get("pages", [])) != page_count:
            mismatched.append(f"PDF page count: {pdf['name']}")
        for extracted_page, page in zip(pages, pdf.get("pages", [])):
            rendered = extracted_page.rstrip("\n")
            expected_hash = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
            page_path = references / page["file"]
            generated_files.add(page["file"])
            if not page_path.is_file():
                missing.append(page["file"])
                continue
            source_hash, extracted_hash, payload = markdown_payload(page_path)
            if (
                source_hash != pdf["sha256"]
                or extracted_hash != expected_hash
                or page["text_sha256"] != expected_hash
                or page["bytes"] != len(rendered.encode("utf-8"))
                or payload != rendered
            ):
                mismatched.append(f"PDF generated payload: {page['file']}")
        pdf_index = references / pdf["index_file"]
        if not pdf_index.is_file():
            missing.append(pdf["index_file"])
        elif markdown_link_targets(pdf_index) != {item["file"] for item in pdf.get("pages", [])}:
            mismatched.append(f"PDF index links: {pdf['index_file']}")

    if markdown_link_targets(index_path) != expected_top_indexes:
        mismatched.append("top-level manual index links")

    actual_generated = {
        path.name
        for pattern in ("official-input-*.md", "official-guide-*.md", "official-release-notes-*.md", "official-pdf-*.md")
        for path in references.glob(pattern)
        if not path.name.endswith("-index.md")
    }
    if actual_generated != generated_files:
        mismatched.append(
            f"generated file set differs; stale={sorted(actual_generated - generated_files)}, "
            f"absent={sorted(generated_files - actual_generated)}"
        )

    forbidden = [
        "DFT-" + "Skills-Bank",
        "DFT-" + "Software-Knowledge",
        "Documents/projects/" + "DFT",
        "/" + "Users/",
        "/" + "Volumes/",
    ]
    for path in [skill_root / "SKILL.md", skill_root / "agents" / "openai.yaml", *skill_root.glob("scripts/*.py")]:
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        for value in forbidden:
            if value in content:
                mismatched.append(f"forbidden local source reference {value}: {path}")

    if missing:
        raise RuntimeError("Missing mirror files:\n" + "\n".join(sorted(set(missing))))
    if mismatched:
        raise RuntimeError("Official mirror integrity errors:\n" + "\n".join(mismatched))
    print(
        json.dumps(
            {
                "input_manuals": len(manifest["input_manuals"]),
                "input_sections": sum(len(item["sections"]) for item in manifest["input_manuals"]),
                "user_guides": len(manifest.get("user_guides", [])),
                "guide_pages": sum(len(item["pages"]) for item in manifest.get("user_guides", [])),
                "release_note_sections": len(manifest["release_notes"]["sections"]),
                "pdf_manuals": len(manifest["pdf_manuals"]),
                "pdf_pages": sum(item["page_count"] for item in manifest["pdf_manuals"]),
                "retrieval_mode": manifest["retrieval_mode"],
                "status": "ok",
            },
            indent=2,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Fetch every official source live in staging; replace the mirror only after validation",
    )
    args = parser.parse_args()
    if args.check:
        check(args.skill_root)
    else:
        sync(args.skill_root, refresh=args.refresh)
        check(args.skill_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
