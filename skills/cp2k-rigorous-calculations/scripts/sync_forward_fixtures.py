#!/usr/bin/env python3
"""Refresh or verify privacy-sanitized fixtures from an official CP2K tool repository."""

from __future__ import annotations

import argparse
import certifi
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import ssl
import urllib.request
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_ROOT = SKILL_ROOT / "references" / "forward-fixtures"
MANIFEST_PATH = FIXTURE_ROOT / "manifest.json"
OUTPUT_PATH = FIXTURE_ROOT / "cp2k-9.0-energy-force.sanitized.out"
LICENSE_PATH = FIXTURE_ROOT / "LICENSE.cp2k-output-tools.txt"
SOURCE_REPOSITORY = "https://github.com/cp2k/cp2k-output-tools"
SOURCE_COMMIT = "403cc70966d7284d9f71f56b8cd2ae08f969fa62"
OUTPUT_URL = f"https://raw.githubusercontent.com/cp2k/cp2k-output-tools/{SOURCE_COMMIT}/tests/outputs/Si_bulk8.out"
LICENSE_URL = f"https://raw.githubusercontent.com/cp2k/cp2k-output-tools/{SOURCE_COMMIT}/LICENSE"
OUTPUT_RAW_SHA256 = "6cd1b325cf89fb925af3eaf62580e42a95c1c4f1b5a6e70b8e00b517c0296ed2"
MAX_BYTES = 2 * 1024 * 1024
LINE_REDACTIONS = (
    (re.compile(r"(?m)^(.*PROGRAM STARTED ON\s+).*$"), r"\1fixture-host", 1),
    (re.compile(r"(?m)^(.*PROGRAM STARTED BY\s+).*$"), r"\1fixture-user", 1),
    (re.compile(r"(?m)^(.*PROGRAM STARTED IN\s+).*$"), r"\1<redacted-case-path>", 1),
    (re.compile(r"(?m)^(.*PROGRAM RAN ON\s+).*$"), r"\1fixture-host", 1),
    (re.compile(r"(?m)^(.*PROGRAM RAN BY\s+).*$"), r"\1fixture-user", 1),
    (re.compile(r"(?m)^(.*PROGRAM STOPPED IN\s+).*$"), r"\1<redacted-case-path>", 1),
    (re.compile(r"(?m)^(.*PROGRAM PROCESS ID\s+).*$"), r"\g<1>00000", 2),
    (re.compile(r"(?m)^(\s*Local host:\s+).*$"), r"\1fixture-host", 1),
    (re.compile(r"(?m)^(\s*CP2K\| Program compiled on\s+).*$"), r"\1fixture-host", 1),
    (re.compile(r"(?m)^(\s*CP2K\| Program compiled for\s+).*$"), r"\1<redacted-build-target>", 1),
    (re.compile(r"(?m)^(\s*CP2K\| Data directory path\s+).*$"), r"\1<redacted-data-path>", 1),
    (re.compile(r"(?m)^(\s*CP2K\| Input file name\s+).*$"), r"\1fixture.inp", 1),
    (re.compile(r"(?m)^(\s*GLOBAL\| Project name\s+).*$"), r"\1fixture-project", 1),
    (re.compile(r"(?m)^(\s*GLOBAL\| CPU model name\s+).*$"), r"\1<redacted-cpu-model>", 1),
    (re.compile(r"(?m)^\[[^]\r\n]+:[0-9]+\]"), "[fixture-host:00000]", 2),
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Vibe-DFT-Skills/CP2K-fixture-sync"})
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, timeout=30, context=context) as response:
        final_url = response.geturl()
        if not final_url.startswith("https://raw.githubusercontent.com/cp2k/cp2k-output-tools/"):
            raise ValueError("fixture download redirected outside the pinned official repository")
        body = response.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError("official fixture exceeds the bounded download size")
    return body


def sanitize_output(raw: bytes) -> tuple[bytes, int]:
    text = raw.decode("utf-8")
    source_identities = set(
        match.group(1).strip()
        for pattern in (
            re.compile(r"(?m)^\s*Local host:\s+(\S+)$"),
            re.compile(r"(?m)^.*PROGRAM STARTED BY\s+(\S+)$"),
        )
        for match in pattern.finditer(text)
    )
    replacements = 0
    for pattern, replacement, expected_count in LINE_REDACTIONS:
        text, count = pattern.subn(replacement, text)
        if count != expected_count:
            raise ValueError("pinned fixture no longer matches the expected privacy-redaction grammar")
        replacements += count
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
    if any(value and value in text for value in source_identities):
        raise ValueError("sanitized fixture retains a source host or account identifier")
    sanitized = text.encode("utf-8")
    validate_sanitized(sanitized)
    return sanitized, replacements


def validate_sanitized(body: bytes) -> None:
    text = body.decode("utf-8")
    if re.search(r"/(?:Users|home|users|data)/", text):
        raise ValueError("sanitized fixture retains a forbidden host, account, or private path token")


def refresh() -> dict[str, Any]:
    raw_output = fetch(OUTPUT_URL)
    if sha256_bytes(raw_output) != OUTPUT_RAW_SHA256:
        raise ValueError("pinned official output SHA-256 differs from the expected source hash")
    sanitized, redactions = sanitize_output(raw_output)
    license_body = fetch(LICENSE_URL)
    FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_bytes(sanitized)
    LICENSE_PATH.write_bytes(license_body)
    manifest = {
        "schema_version": "1.0",
        "source_repository": SOURCE_REPOSITORY,
        "source_commit": SOURCE_COMMIT,
        "retrieved_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "license": "MIT",
        "license_file": LICENSE_PATH.name,
        "license_sha256": sha256_bytes(license_body),
        "fixtures": [
            {
                "file": OUTPUT_PATH.name,
                "source_path": "tests/outputs/Si_bulk8.out",
                "source_url": OUTPUT_URL,
                "source_sha256": OUTPUT_RAW_SHA256,
                "sanitized_sha256": sha256_bytes(sanitized),
                "bytes": len(sanitized),
                "redaction_count": redactions,
                "normalization": "trailing-whitespace-removed",
                "classification": "real-artifact-derived-privacy-sanitized",
                "maturity_ceiling": "format-fixture-validated",
                "cp2k_version": "9.0-development",
            }
        ],
        "limitations": [
            "The fixture is from CP2K 9.0 development output and does not validate CP2K 2026.2 behavior.",
            "Privacy sanitization preserves tested markers but prevents treating the file as an untouched real artifact.",
            "The source run contains runtime/MPI warning text and is a negative forward fixture, not accepted scientific evidence.",
        ],
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def check() -> dict[str, Any]:
    errors: list[str] = []
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"status": "blocked", "errors": ["fixture manifest is missing or invalid"]}
    if manifest.get("schema_version") != "1.0" or manifest.get("source_commit") != SOURCE_COMMIT:
        errors.append("fixture manifest schema or source commit differs")
    records = manifest.get("fixtures")
    if not isinstance(records, list) or len(records) != 1 or not isinstance(records[0], dict):
        errors.append("fixture manifest must contain exactly one fixture record")
    else:
        record = records[0]
        try:
            body = OUTPUT_PATH.read_bytes()
            if sha256_bytes(body) != record.get("sanitized_sha256") or len(body) != record.get("bytes"):
                errors.append("sanitized fixture hash or size differs from manifest")
            validate_sanitized(body)
        except OSError:
            errors.append("sanitized fixture is missing")
        except ValueError as exc:
            errors.append(str(exc))
    try:
        if sha256_bytes(LICENSE_PATH.read_bytes()) != manifest.get("license_sha256"):
            errors.append("fixture license hash differs from manifest")
    except OSError:
        errors.append("fixture license is missing")
    return {
        "status": "ok" if not errors else "blocked",
        "errors": errors,
        "source_commit": SOURCE_COMMIT,
        "fixture_count": 1 if not errors else 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--refresh", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = refresh() if args.refresh else check()
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if args.refresh or result["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
