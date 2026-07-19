#!/usr/bin/env python3
"""Audit repository paths for copied files, cache artifacts, and routing hazards."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Iterable, Sequence

from registry_yaml import RegistryYAMLError, load_yaml_strict


EXIT_OK = 0
EXIT_FINDINGS = 2

COPY_SUFFIX_PATH = "HYGIENE_COPY_SUFFIX_PATH"
DUPLICATE_FILE_IDENTICAL = "HYGIENE_DUPLICATE_FILE_IDENTICAL"
DUPLICATE_FILE_DIVERGED = "HYGIENE_DUPLICATE_FILE_DIVERGED"
EMPTY_COPIED_DIRECTORY = "HYGIENE_EMPTY_COPIED_DIRECTORY"
PLANNED_SKILL_DIRECTORY = "HYGIENE_PLANNED_SKILL_DIRECTORY"
VISIBLE_CACHE_ARTIFACT = "HYGIENE_VISIBLE_CACHE_ARTIFACT"
ABNORMAL_SKILL_FILENAME = "HYGIENE_ABNORMAL_SKILL_FILENAME"
GIT_SCAN_FAILED = "HYGIENE_GIT_SCAN_FAILED"
SKILL_REGISTRY_INVALID = "HYGIENE_SKILL_REGISTRY_INVALID"

# Finder commonly produces ``name copy.ext`` and later numbered copies.  Some
# synced filesystems instead produce ``name 2.ext``; that exact form is present
# in the repository this gate was introduced to protect.  Limit bare numeric
# suffixes to 2..99 to avoid treating year-like names as copies.
_COPY_SUFFIX = re.compile(
    r"^(?P<base>.+?)(?P<marker> "
    r"(?:(?:[2-9]|[1-9][0-9])|copy(?: (?:[2-9]|[1-9][0-9]))?|"
    r"副本(?: (?:[2-9]|[1-9][0-9]))?|\((?:[1-9]|[1-9][0-9])\)))"
    r"(?P<suffix>(?:\.[^./]+)*)$",
    re.IGNORECASE,
)

_CACHE_DIRECTORIES = {
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
}
_CACHE_FILES = {".coverage", ".DS_Store"}
_BYTECODE_SUFFIXES = {".pyc", ".pyo", ".pyd"}


@dataclass(frozen=True, order=True)
class Finding:
    """A deterministic repository hygiene finding."""

    code: str
    path: str
    related_path: str = ""
    detail: str = ""

    def render(self) -> str:
        fields = [self.code, self.path]
        if self.related_path:
            fields.append(f"related={self.related_path}")
        if self.detail:
            fields.append(self.detail)
        return "\t".join(fields)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run_git(root: Path, arguments: Sequence[str]) -> tuple[int, bytes, str]:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr.decode(errors="replace").strip()


def _decode_paths(payload: bytes) -> set[str]:
    return {
        os.fsdecode(item)
        for item in payload.split(b"\0")
        if item
    }


def _git_visible_files(root: Path, include_ignored: bool) -> tuple[set[str], list[Finding]]:
    code, payload, error = _run_git(
        root,
        ["ls-files", "-z", "--cached", "--others", "--exclude-standard"],
    )
    if code != 0:
        detail = error or f"git ls-files exited {code}"
        return set(), [Finding(GIT_SCAN_FAILED, ".", detail=detail)]

    paths = _decode_paths(payload)
    if not include_ignored:
        return paths, []

    ignored_code, ignored_payload, ignored_error = _run_git(
        root,
        ["ls-files", "-z", "--others", "--ignored", "--exclude-standard"],
    )
    if ignored_code != 0:
        detail = ignored_error or f"git ls-files --ignored exited {ignored_code}"
        return paths, [Finding(GIT_SCAN_FAILED, ".", detail=detail)]
    paths.update(_decode_paths(ignored_payload))
    return paths, []


def _copy_canonical_name(name: str) -> str | None:
    match = _COPY_SUFFIX.fullmatch(name)
    if match is None:
        return None
    return f"{match.group('base')}{match.group('suffix')}"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_cache_artifact(relative: Path) -> bool:
    if relative.name in _CACHE_FILES or relative.suffix.lower() in _BYTECODE_SUFFIXES:
        return True
    return any(part in _CACHE_DIRECTORIES for part in relative.parts)


def _is_abnormal_skill_filename(relative: Path) -> bool:
    if len(relative.parts) != 3 or relative.parts[0] != "skills":
        return False
    name = relative.name
    return name.lower().startswith("skill") and name.lower().endswith(".md") and name != "SKILL.md"


def _is_git_ignored(root: Path, relative: Path) -> bool:
    code, _, _ = _run_git(root, ["check-ignore", "--quiet", "--", relative.as_posix()])
    return code == 0


def _copy_named_directories(root: Path, include_ignored: bool) -> Iterable[Path]:
    for directory, child_directories, _ in os.walk(root, topdown=True):
        current = Path(directory)
        selected_children: list[str] = []
        for name in sorted(child_directories):
            if name == ".git":
                continue
            relative = (current / name).relative_to(root)
            if not include_ignored and _is_git_ignored(root, relative):
                continue
            selected_children.append(name)
        child_directories[:] = selected_children
        for name in child_directories:
            if _copy_canonical_name(name) is None:
                continue
            candidate = current / name
            relative = candidate.relative_to(root)
            yield relative


def _planned_skill_names(
    root: Path,
    skill_data: dict[str, Any] | None = None,
) -> tuple[set[str], list[Finding]]:
    registry = root / "registry" / "skill-registry.yaml"
    try:
        data = (
            skill_data
            if skill_data is not None
            else load_yaml_strict(registry, "skill-registry.yaml")
        )
        skills = data["skills"]
        if not isinstance(skills, dict):
            raise TypeError("skills must be a mapping")
        planned = {
            name
            for name, specification in skills.items()
            if isinstance(name, str)
            and isinstance(specification, dict)
            and specification.get("lifecycle") == "planned"
        }
    except (RegistryYAMLError, KeyError, TypeError) as exc:
        return set(), [Finding(SKILL_REGISTRY_INVALID, "registry/skill-registry.yaml", detail=str(exc))]
    return planned, []


def audit_repository(
    root: Path | None = None,
    *,
    include_ignored: bool = False,
    skill_data: dict[str, Any] | None = None,
) -> list[Finding]:
    """Return stable findings for the selected repository without modifying it."""

    selected_root = (root or repo_root()).resolve()
    visible_files, findings = _git_visible_files(selected_root, include_ignored)

    for relative_text in sorted(visible_files):
        relative = Path(relative_text)
        source = selected_root / relative
        if not source.is_file():
            continue

        if _is_cache_artifact(relative):
            findings.append(
                Finding(
                    VISIBLE_CACHE_ARTIFACT,
                    relative.as_posix(),
                    detail="tracked or selected by the current Git visibility policy",
                )
            )

        if _is_abnormal_skill_filename(relative):
            findings.append(
                Finding(
                    ABNORMAL_SKILL_FILENAME,
                    relative.as_posix(),
                    detail="the only valid root instruction filename is SKILL.md",
                )
            )

        canonical_name = _copy_canonical_name(relative.name)
        if canonical_name is None:
            continue
        canonical_relative = relative.with_name(canonical_name)
        canonical = selected_root / canonical_relative
        if not canonical.is_file():
            findings.append(
                Finding(
                    COPY_SUFFIX_PATH,
                    relative.as_posix(),
                    related_path=canonical_relative.as_posix(),
                    detail="copy-like suffix has no canonical peer",
                )
            )
            continue

        source_hash = _sha256(source)
        canonical_hash = _sha256(canonical)
        finding_code = (
            DUPLICATE_FILE_IDENTICAL
            if source_hash == canonical_hash
            else DUPLICATE_FILE_DIVERGED
        )
        findings.append(
            Finding(
                finding_code,
                relative.as_posix(),
                related_path=canonical_relative.as_posix(),
                detail=f"sha256={source_hash}; canonical_sha256={canonical_hash}",
            )
        )

    for relative in sorted(set(_copy_named_directories(selected_root, include_ignored))):
        directory = selected_root / relative
        canonical_name = _copy_canonical_name(relative.name)
        canonical_relative = relative.with_name(canonical_name) if canonical_name else relative
        try:
            empty = not any(directory.iterdir())
        except OSError:
            empty = False
        findings.append(
            Finding(
                EMPTY_COPIED_DIRECTORY if empty else COPY_SUFFIX_PATH,
                relative.as_posix(),
                related_path=canonical_relative.as_posix(),
                detail="empty copy-like directory" if empty else "copy-like directory name",
            )
        )

    planned_skills, registry_findings = _planned_skill_names(selected_root, skill_data)
    findings.extend(registry_findings)
    for name in sorted(planned_skills):
        relative = Path("skills") / name
        if os.path.lexists(selected_root / relative):
            findings.append(
                Finding(
                    PLANNED_SKILL_DIRECTORY,
                    relative.as_posix(),
                    detail="planned skills must use path: null and have no source path",
                )
            )

    return sorted(set(findings))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root())
    parser.add_argument(
        "--include-ignored",
        action="store_true",
        help="also inspect Git-ignored files such as bytecode and cache artifacts",
    )
    args = parser.parse_args(argv)

    findings = audit_repository(args.root, include_ignored=args.include_ignored)
    if findings:
        for finding in findings:
            print(finding.render(), file=sys.stderr)
        print(f"FAIL: repository hygiene reported {len(findings)} finding(s)", file=sys.stderr)
        return EXIT_FINDINGS
    print("PASS: repository hygiene is clean")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
