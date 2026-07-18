#!/usr/bin/env python3
"""Build or verify a version-matched curated CP2K manual snapshot."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import ssl
import tempfile
import time
from typing import Any, Iterable
import urllib.error
from urllib.parse import urldefrag, urljoin, urlsplit
import urllib.request


SKILL_ROOT = Path(__file__).resolve().parent.parent
REFERENCES = SKILL_ROOT / "references"
DEFAULT_REGISTRY = REFERENCES / "official-source-registry.json"
DEFAULT_SNAPSHOT = REFERENCES / "official-manual"
VERSION = re.compile(r"^[0-9]{1,4}\.[0-9]{1,2}$")
ALLOWED_HOST = "manual.cp2k.org"
MAX_PAGE_BYTES = 20 * 1024 * 1024


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


def fetch(url: str, *, timeout: float = 30.0, attempts: int = 3) -> bytes:
    if urlsplit(url).hostname != ALLOWED_HOST or urlsplit(url).scheme != "https":
        raise ValueError("only HTTPS sources from manual.cp2k.org are allowed")
    request = urllib.request.Request(url, headers={"User-Agent": "dft-codex-skills-cp2k-mirror/1.0"})
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
        time.sleep(0.25 * (2**attempt))
    raise RuntimeError("unreachable retry state")


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


def page_to_markdown(topic: str, url: str, body: bytes) -> bytes:
    try:
        from bs4 import BeautifulSoup
    except ModuleNotFoundError as exc:
        raise RuntimeError("beautifulsoup4 is required to refresh the CP2K manual snapshot") from exc
    soup = BeautifulSoup(body, "lxml")
    article = soup.find("article") or soup.find("main") or soup.find(attrs={"role": "main"})
    if article is None:
        raise ValueError(f"official page has no supported main-content element: {topic}")
    for node in article.find_all(["script", "style", "nav", "form"]):
        node.decompose()
    lines: list[str] = []
    for raw in article.get_text("\n").splitlines():
        line = " ".join(raw.split())
        if line and (not lines or lines[-1] != line):
            lines.append(line)
    if len(lines) < 3:
        raise ValueError(f"official page extraction is unexpectedly empty: {topic}")
    text = (
        f"# CP2K official manual snapshot: {topic}\n\n"
        f"- Source: {url}\n"
        f"- Raw SHA-256: {sha256_bytes(body)}\n"
        "- Status: version-matched cached official text; reopen the source for current live verification.\n\n"
        + "\n\n".join(lines)
        + "\n"
    )
    return text.encode("utf-8")


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
    return topic, url, fetch(url)


def refresh_snapshot(
    version: str,
    *,
    registry_path: Path = DEFAULT_REGISTRY,
    snapshot_dir: Path = DEFAULT_SNAPSHOT,
    workers: int = 4,
) -> dict[str, Any]:
    if workers < 1 or workers > 16:
        raise ValueError("workers must be between 1 and 16")
    registry = load_registry(registry_path)
    branch = manual_branch(version)
    root = registry["manual_root"].rstrip("/") + f"/{branch}/"
    genindex_url = root + "genindex.html"
    genindex = fetch(genindex_url, timeout=60.0)
    inventory = discover_index_pages(genindex, genindex_url)
    topic_urls = {
        topic: root + source_path(record, version)
        for topic, record in registry["topics"].items()
    }
    retrieved = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    with tempfile.TemporaryDirectory(prefix="cp2k-manual-stage-", dir=REFERENCES) as temporary:
        stage = Path(temporary) / "official-manual"
        stage.mkdir()
        page_records: dict[str, Any] = {}
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_fetch_topic, item): item[0] for item in topic_urls.items()}
            for future in as_completed(futures):
                try:
                    topic, url, body = future.result()
                except Exception as exc:
                    raise RuntimeError(
                        f"official topic fetch failed: {futures[future]} ({type(exc).__name__})"
                    ) from exc
                rendered = page_to_markdown(topic, url, body)
                filename = f"{topic}.md"
                (stage / filename).write_bytes(rendered)
                page_records[topic] = {
                    "path": filename,
                    "source_url": url,
                    "source_path": source_path(registry["topics"][topic], version),
                    "raw_sha256": sha256_bytes(body),
                    "raw_bytes": len(body),
                    "snapshot_sha256": sha256_bytes(rendered),
                    "snapshot_bytes": len(rendered),
                    "indexed": source_path(registry["topics"][topic], version) in inventory,
                }
        inventory_record = {
            "schema_version": "1.0",
            "manual_version": version,
            "manual_branch": branch,
            "source_url": genindex_url,
            "source_sha256": sha256_bytes(genindex),
            "page_count": len(inventory),
            "pages": inventory,
        }
        inventory_bytes = (json.dumps(inventory_record, indent=2, sort_keys=True) + "\n").encode("utf-8")
        (stage / "index.json").write_bytes(inventory_bytes)
        manifest = {
            "schema_version": "1.0",
            "manual_version": version,
            "manual_branch": branch,
            "retrieved_utc": retrieved,
            "registry_sha256": sha256_file(registry_path),
            "index_sha256": sha256_bytes(inventory_bytes),
            "index_page_count": len(inventory),
            "mirrored_topic_count": len(page_records),
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
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    index = json.loads(index_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if manifest.get("schema_version") != "1.0" or index.get("schema_version") != "1.0":
        errors.append("snapshot schema version is unsupported")
    if manifest.get("manual_version") != index.get("manual_version"):
        errors.append("manifest and index versions differ")
    if manifest.get("manual_branch") != index.get("manual_branch"):
        errors.append("manifest and index branches differ")
    if manifest.get("registry_sha256") != sha256_file(registry_path):
        errors.append("official-source registry changed after snapshot generation")
    if manifest.get("index_sha256") != sha256_file(index_path):
        errors.append("official manual index hash mismatch")
    if index.get("page_count") != len(index.get("pages", [])) or index.get("page_count", 0) < 100:
        errors.append("official manual index is incomplete")
    page_records = manifest.get("pages")
    if not isinstance(page_records, dict) or set(page_records) != set(registry["topics"]):
        errors.append("mirrored topics do not match the source registry")
        page_records = page_records if isinstance(page_records, dict) else {}
    expected_files = {"manifest.json", "index.json"}
    for topic, record in page_records.items():
        filename = record.get("path")
        if not isinstance(filename, str) or filename != f"{topic}.md":
            errors.append(f"invalid snapshot path for topic {topic}")
            continue
        expected_files.add(filename)
        path = snapshot_dir / filename
        if not path.is_file():
            errors.append(f"missing snapshot page for topic {topic}")
        elif sha256_file(path) != record.get("snapshot_sha256"):
            errors.append(f"snapshot hash mismatch for topic {topic}")
    actual_files = {path.name for path in snapshot_dir.iterdir() if path.is_file()}
    if actual_files != expected_files:
        errors.append("snapshot contains missing or unmanifested files")
    return {
        "schema_version": "1.0",
        "status": "ok" if not errors else "blocked",
        "manual_version": manifest.get("manual_version"),
        "manual_branch": manifest.get("manual_branch"),
        "index_page_count": index.get("page_count"),
        "mirrored_topic_count": len(page_records),
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
