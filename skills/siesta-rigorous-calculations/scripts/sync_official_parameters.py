#!/usr/bin/env python3
"""Build or verify a compact FDF index from a pinned official SIESTA source tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any


GENERATOR_VERSION = "1.0.0"
DEFAULT_TAG = "5.4.2"
DEFAULT_COMMIT = "e486d12067b96ff688179f0496d0ec21b6fae0ab"
SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INDEX = SKILL_ROOT / "references" / "official-fdf-index.json"
ENTRY_RE = re.compile(
    r"\\begin\{fdfentry\}\{(?P<label>[^{}]+)\}"
    r"(?:\[(?P<value_type>[^\]]*)\])?"
    r"(?:<(?P<default>.*)>)?\s*%?\s*$"
)
LOGICAL_RE = re.compile(r"\\begin\{fdflogical(?P<default>[TF])\}\{(?P<label>[^{}]+)\}")
VERSION_RE = re.compile(r"^\d+(?:\.\d+){1,2}$")
COMMIT_RE = re.compile(r"^[a-f0-9]{40}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_label(label: str) -> str:
    return re.sub(r"\s+", "", label.replace("!", ".").strip())


def lookup_key(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize_label(label).casefold())


def git_value(source_tree: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(source_tree), *arguments],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def parse_manual(source_tree: Path, *, source_tag: str, expected_commit: str) -> dict[str, Any]:
    if not VERSION_RE.fullmatch(source_tag):
        raise ValueError("source tag must be an explicit dotted numeric SIESTA version")
    if not COMMIT_RE.fullmatch(expected_commit):
        raise ValueError("expected commit must be a lowercase 40-character Git hash")
    observed_commit = git_value(source_tree, "rev-parse", "HEAD")
    if observed_commit != expected_commit:
        raise ValueError("official source checkout does not match the pinned commit")
    if git_value(source_tree, "status", "--short"):
        raise ValueError("official source checkout is not clean")

    sections_root = source_tree / "Docs" / "tex" / "sections"
    if not sections_root.is_dir():
        raise ValueError("official source tree has no Docs/tex/sections directory")

    entries: list[dict[str, Any]] = []
    source_paths: set[Path] = set()
    occurrences: dict[str, list[str]] = {}
    for path in sorted(sections_root.rglob("*.tex")):
        relative = path.relative_to(source_tree).as_posix()
        disabled_depth = 0
        active_lines: list[tuple[int, str]] = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith(r"\iffalse"):
                disabled_depth += 1
                continue
            if disabled_depth and stripped.startswith(r"\fi"):
                disabled_depth -= 1
                continue
            if disabled_depth or stripped.startswith("%"):
                continue
            active_lines.append((line_number, line))
        for position, (line_number, line) in enumerate(active_lines):
            candidate = line
            if r"\begin{fdfentry}" in line and ENTRY_RE.search(candidate) is None:
                for _, continuation in active_lines[position + 1 : position + 8]:
                    candidate += " " + continuation.strip()
                    if ENTRY_RE.search(candidate) is not None:
                        break
            entry_match = ENTRY_RE.search(candidate)
            logical_match = LOGICAL_RE.search(line)
            if entry_match:
                label = normalize_label(entry_match.group("label"))
                value_type = (entry_match.group("value_type") or "unspecified").strip()
                documented_default = (entry_match.group("default") or "").strip() or None
                source_macro = "fdfentry"
            elif logical_match:
                label = normalize_label(logical_match.group("label"))
                value_type = "logical"
                documented_default = "true" if logical_match.group("default") == "T" else "false"
                source_macro = f"fdflogical{logical_match.group('default')}"
            else:
                continue
            key = lookup_key(label)
            if not key:
                raise ValueError(f"empty normalized FDF label at {relative}:{line_number}")
            occurrences.setdefault(key, []).append(f"{relative}:{line_number}")
            source_paths.add(path)
            entries.append(
                {
                    "label": label,
                    "lookup_key": key,
                    "value_type": value_type,
                    "documented_default_tex": documented_default,
                    "source_macro": source_macro,
                    "source_file": relative,
                    "source_line": line_number,
                    "source_url": f"https://gitlab.com/siesta-project/siesta/-/blob/{expected_commit}/{relative}#L{line_number}",
                }
            )

    entries.sort(key=lambda item: (item["lookup_key"], item["label"]))
    source_files = []
    for path in sorted(source_paths):
        relative = path.relative_to(source_tree).as_posix()
        source_files.append(
            {
                "path": relative,
                "sha256": sha256_file(path),
                "raw_url": f"https://gitlab.com/siesta-project/siesta/-/raw/{expected_commit}/{relative}",
            }
        )
    commit_utc = git_value(source_tree, "show", "-s", "--format=%cI", expected_commit)
    documentation_line = ".".join(source_tag.split(".")[:2])
    ambiguous_lookup_keys = sorted(key for key, locations in occurrences.items() if len(locations) > 1)
    return {
        "schema_version": "1.0",
        "generator": "sync_official_parameters.py",
        "generator_version": GENERATOR_VERSION,
        "code": "siesta",
        "code_version": source_tag,
        "documentation_line": documentation_line,
        "source_project": "https://gitlab.com/siesta-project/siesta",
        "source_tag": source_tag,
        "source_commit": expected_commit,
        "source_commit_utc": commit_utc,
        "entry_count": len(entries),
        "ambiguous_lookup_keys": ambiguous_lookup_keys,
        "source_file_count": len(source_files),
        "source_files": source_files,
        "entries": entries,
        "limitations": [
            "This index preserves FDF entry headers, types, documented defaults, and pinned source locations; it does not replace the surrounding official explanation.",
            "A documented default is software behavior, not a scientific convergence recommendation.",
            "Labels observed only in released source code but absent from the manual require separate source-level evidence.",
        ],
    }


def validate_index(index: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "schema_version",
        "generator",
        "generator_version",
        "code",
        "code_version",
        "documentation_line",
        "source_project",
        "source_tag",
        "source_commit",
        "source_commit_utc",
        "entry_count",
        "ambiguous_lookup_keys",
        "source_file_count",
        "source_files",
        "entries",
        "limitations",
    }
    if set(index) != required:
        errors.append("top-level fields do not match the official index schema")
    if index.get("schema_version") != "1.0" or index.get("generator") != "sync_official_parameters.py":
        errors.append("unsupported official index producer or schema")
    if index.get("code") != "siesta" or not VERSION_RE.fullmatch(str(index.get("code_version", ""))):
        errors.append("official index has an invalid code/version binding")
    if not COMMIT_RE.fullmatch(str(index.get("source_commit", ""))):
        errors.append("official index has an invalid source commit")
    entries = index.get("entries")
    sources = index.get("source_files")
    if not isinstance(entries, list) or index.get("entry_count") != len(entries):
        errors.append("entry count is inconsistent")
        entries = []
    if not isinstance(sources, list) or index.get("source_file_count") != len(sources):
        errors.append("source-file count is inconsistent")
        sources = []
    source_names: set[str] = set()
    for source in sources:
        if not isinstance(source, dict) or set(source) != {"path", "sha256", "raw_url"}:
            errors.append("a source-file record is malformed")
            continue
        if not re.fullmatch(r"[a-f0-9]{64}", str(source.get("sha256", ""))):
            errors.append("a source-file hash is invalid")
        source_names.add(str(source.get("path")))
    key_counts: dict[str, int] = {}
    for entry in entries:
        expected_fields = {
            "label",
            "lookup_key",
            "value_type",
            "documented_default_tex",
            "source_macro",
            "source_file",
            "source_line",
            "source_url",
        }
        if not isinstance(entry, dict) or set(entry) != expected_fields:
            errors.append("an FDF entry record is malformed")
            continue
        key = str(entry.get("lookup_key", ""))
        if not key or key != lookup_key(str(entry.get("label", ""))):
            errors.append("an FDF entry has an invalid lookup key")
        key_counts[key] = key_counts.get(key, 0) + 1
        if entry.get("source_file") not in source_names or not isinstance(entry.get("source_line"), int):
            errors.append("an FDF entry is not bound to a source-file record")
    observed_ambiguous = sorted(key for key, count in key_counts.items() if count > 1)
    if index.get("ambiguous_lookup_keys") != observed_ambiguous:
        errors.append("ambiguous lookup-key metadata is inconsistent")
    return sorted(set(errors))


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    if not path.parent.is_dir():
        raise ValueError("output parent directory does not exist")
    rendered = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        handle.write(rendered)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-tree", type=Path)
    parser.add_argument("--source-tag", default=DEFAULT_TAG)
    parser.add_argument("--expected-commit", default=DEFAULT_COMMIT)
    parser.add_argument("--out", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            current = json.loads(args.out.read_text(encoding="utf-8"))
            errors = validate_index(current)
            if args.source_tree is not None:
                rebuilt = parse_manual(args.source_tree, source_tag=args.source_tag, expected_commit=args.expected_commit)
                if rebuilt != current:
                    errors.append("committed official index differs from the pinned source tree")
            if errors:
                raise ValueError("; ".join(sorted(set(errors))))
            print(json.dumps({"status": "ok", "entries": current["entry_count"], "source_files": current["source_file_count"], "source_commit": current["source_commit"]}, sort_keys=True))
            return 0
        if args.source_tree is None:
            raise ValueError("--source-tree is required when rebuilding the official index")
        payload = parse_manual(args.source_tree, source_tag=args.source_tag, expected_commit=args.expected_commit)
        errors = validate_index(payload)
        if errors:
            raise ValueError("; ".join(errors))
        atomic_write_json(args.out, payload)
        print(json.dumps({"status": "written", "entries": payload["entry_count"], "source_files": payload["source_file_count"], "out": args.out.name}, sort_keys=True))
        return 0
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "blocked", "error_type": type(exc).__name__, "message": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
