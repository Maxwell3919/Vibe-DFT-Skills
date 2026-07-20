#!/usr/bin/env python3
"""Audit tracked repository content and reachable history for private or restricted material."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Sequence


MAX_TEXT_BYTES = 8 * 1024 * 1024
SENSITIVE_BASENAMES = frozenset(
    {
        ".env",
        "POTCAR",
        "WAVECAR",
        "CHGCAR",
        "AECCAR0",
        "AECCAR1",
        "AECCAR2",
        "PROCAR",
        "IBZKPT",
    }
)
SENSITIVE_SUFFIXES = frozenset(
    {".pem", ".p12", ".pfx", ".kdbx", ".wfc", ".chk", ".gbw", ".psctr"}
)
RESTRICTED_MARKERS = (
    b"TITEL  = PAW_",
    b"VRHFIN =",
    b"End of Dataset",
    b"-----BEGIN OPENSSH PRIVATE KEY-----",
    b"-----BEGIN PRIVATE KEY-----",
)
HIGH_CONFIDENCE_PATTERNS = (
    ("PRIVATE_KEY", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    ("AWS_ACCESS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GITHUB_TOKEN", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("OPENAI_TOKEN", re.compile(r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}\b")),
    ("BEARER_TOKEN", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{24,}", re.IGNORECASE)),
)
SECRET_ASSIGNMENT = re.compile(
    r"\b(password|passwd|api[_-]?key|secret|access[_-]?token)\s*[:=]\s*"
    r"([\"']?)([^\s,\"'}]{8,})\2",
    re.IGNORECASE,
)
ABSOLUTE_PRIVATE_PATH = re.compile(
    r"(?:^|[\s\"'=:(\[])"
    r"(?P<path>"
    r"/home/(?!runner(?:/|$)|user(?:/|$)|<)[A-Za-z0-9._-]+/"
    r"|/Users/(?!Shared(?:/|$)|<)[A-Za-z0-9._-]+/"
    r"|/(?:scratch|gpfs|lustre|project|work)/(?!<)[A-Za-z0-9._-]+/"
    r")"
)
STRUCTURED_SUFFIXES = frozenset(
    {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".txt", ".md"}
)
SECRET_ASSIGNMENT_SUFFIXES = frozenset(
    {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"}
)
# These exact source and test files intentionally define high-confidence
# signatures or negative fixtures. They remain subject to path and assignment
# checks; only literal signature matching is suppressed.
SIGNATURE_LITERAL_PATHS = frozenset(
    {
        "tools/audit_privacy.py",
        "tools/validate_bundle.py",
        "skills/catmap-microkinetics/scripts/catmap_guard.py",
        "skills/lobster-bonding-analysis/scripts/lobster_guard.py",
        "tests/test_bundle_validation.py",
        "tests/test_repository_privacy.py",
        "tests/test_run_manifest_security_migration.py",
        "tests/test_semantic_validation.py",
    }
)
# Policy files necessarily name restricted classes and placeholder examples.
POLICY_EXCLUDED_PATHS = frozenset(
    {
        "AGENTS.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "docs/branch-protection-policy.md",
        "docs/release-policy.md",
    }
)
# Versioned official-source mirrors may reproduce upstream example paths. This
# exception applies only to absolute-path detection; hashes and source-manifest
# checks remain owned by the existing official-mirror validators.
ABSOLUTE_PATH_EXCLUDED_PREFIXES = (
    "skills/cp2k-rigorous-calculations/references/official-manual/",
    "skills/qe-rigorous-calculations/references/official-",
    "skills/vasp-rigorous-calculations/references/official-wiki/",
)
SAFE_SECRET_WORDS = (
    "example",
    "dummy",
    "redacted",
    "placeholder",
    "synthetic",
    "changeme",
    "<",
    "${",
    "none",
    "null",
)


@dataclass(frozen=True, order=True)
class Finding:
    code: str
    path: str
    detail: str
    commit: str = ""

    def render(self) -> str:
        fields = [self.code, self.path]
        if self.commit:
            fields.append(f"commit={self.commit}")
        fields.append(self.detail)
        return "\t".join(fields)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git(root: Path, arguments: Sequence[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _tracked_paths(root: Path) -> tuple[list[str], list[Finding]]:
    completed = _git(root, ["ls-files", "-z"])
    if completed.returncode != 0:
        detail = completed.stderr.decode(errors="replace").strip() or "git ls-files failed"
        return [], [Finding("PRIVACY_GIT_SCAN_FAILED", ".", detail)]
    paths = sorted(
        value.decode(errors="surrogateescape")
        for value in completed.stdout.split(b"\0")
        if value
    )
    return paths, []


def _unsafe_path_reason(path_text: str) -> str | None:
    path = PurePosixPath(path_text)
    if path.name in SENSITIVE_BASENAMES:
        return f"restricted or raw runtime basename '{path.name}'"
    if path.suffix.lower() in SENSITIVE_SUFFIXES:
        return f"restricted or credential-bearing suffix '{path.suffix.lower()}'"
    if any(part.endswith(".save") for part in path.parts):
        return "raw code save directory content is forbidden"
    return None


def _decode_text(raw: bytes) -> str | None:
    if b"\x00" in raw:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _signature_exempt(path_text: str) -> bool:
    return path_text in SIGNATURE_LITERAL_PATHS


def _absolute_path_exempt(path_text: str) -> bool:
    return path_text.startswith(ABSOLUTE_PATH_EXCLUDED_PREFIXES)


def _content_findings(path_text: str, raw: bytes, *, commit: str = "") -> list[Finding]:
    if path_text in POLICY_EXCLUDED_PATHS:
        return []
    findings: list[Finding] = []
    if not _signature_exempt(path_text):
        for marker in RESTRICTED_MARKERS:
            if marker in raw:
                findings.append(
                    Finding(
                        "PRIVACY_RESTRICTED_PAYLOAD",
                        path_text,
                        f"restricted marker {marker[:40]!r} is present",
                        commit,
                    )
                )
    text = _decode_text(raw)
    if text is None:
        return findings
    if not _signature_exempt(path_text):
        for code, pattern in HIGH_CONFIDENCE_PATTERNS:
            for match in pattern.finditer(text):
                findings.append(
                    Finding(
                        f"PRIVACY_{code}",
                        path_text,
                        f"high-confidence secret signature at character {match.start()}",
                        commit,
                    )
                )
    suffix = PurePosixPath(path_text).suffix.lower()
    if suffix in SECRET_ASSIGNMENT_SUFFIXES:
        for match in SECRET_ASSIGNMENT.finditer(text):
            value = match.group(3).lower()
            if any(word in value for word in SAFE_SECRET_WORDS):
                continue
            findings.append(
                Finding(
                    "PRIVACY_SECRET_ASSIGNMENT",
                    path_text,
                    f"non-placeholder value assigned to {match.group(1)}",
                    commit,
                )
            )
    if suffix in STRUCTURED_SUFFIXES and not _absolute_path_exempt(path_text):
        for match in ABSOLUTE_PRIVATE_PATH.finditer(text):
            findings.append(
                Finding(
                    "PRIVACY_ABSOLUTE_PRIVATE_PATH",
                    path_text,
                    f"private absolute path prefix {match.group('path')!r}",
                    commit,
                )
            )
    return findings


def scan_worktree(root: Path) -> list[Finding]:
    paths, findings = _tracked_paths(root)
    for path_text in paths:
        reason = _unsafe_path_reason(path_text)
        if reason is not None:
            findings.append(Finding("PRIVACY_RESTRICTED_PATH", path_text, reason))
        path = root.joinpath(*PurePosixPath(path_text).parts)
        try:
            if path.is_symlink() or not path.is_file():
                continue
            if path.stat().st_size > MAX_TEXT_BYTES:
                findings.append(
                    Finding(
                        "PRIVACY_LARGE_TRACKED_FILE",
                        path_text,
                        f"tracked file exceeds {MAX_TEXT_BYTES} bytes",
                    )
                )
                continue
            raw = path.read_bytes()
        except OSError as exc:
            findings.append(Finding("PRIVACY_FILE_UNREADABLE", path_text, type(exc).__name__))
            continue
        findings.extend(_content_findings(path_text, raw))
    return sorted(set(findings))


def _history_commits(root: Path) -> tuple[list[str], list[Finding]]:
    completed = _git(root, ["rev-list", "--all"])
    if completed.returncode != 0:
        detail = completed.stderr.decode(errors="replace").strip() or "git rev-list failed"
        return [], [Finding("PRIVACY_HISTORY_SCAN_FAILED", ".", detail)]
    return [line for line in completed.stdout.decode().splitlines() if line], []


def scan_history(root: Path) -> list[Finding]:
    commits, findings = _history_commits(root)
    seen_paths: set[tuple[str, str]] = set()
    for commit in commits:
        tree = _git(root, ["ls-tree", "-r", "--name-only", "-z", commit])
        if tree.returncode != 0:
            findings.append(
                Finding("PRIVACY_HISTORY_SCAN_FAILED", ".", "git ls-tree failed", commit)
            )
            continue
        for raw_path in tree.stdout.split(b"\0"):
            if not raw_path:
                continue
            path_text = raw_path.decode(errors="surrogateescape")
            reason = _unsafe_path_reason(path_text)
            if reason is not None and (commit, path_text) not in seen_paths:
                seen_paths.add((commit, path_text))
                findings.append(
                    Finding("PRIVACY_RESTRICTED_PATH_HISTORY", path_text, reason, commit)
                )

    grep_expression = (
        r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"
        r"|AKIA[0-9A-Z]{16}"
        r"|gh[pousr]_[A-Za-z0-9]{20,}"
        r"|sk-(proj-|svcacct-)?[A-Za-z0-9_-]{20,}"
    )
    for commit in commits:
        completed = _git(
            root,
            ["grep", "-I", "-n", "-E", "-e", grep_expression, commit, "--"],
        )
        if completed.returncode not in (0, 1):
            detail = completed.stderr.decode(errors="replace").strip() or "git grep failed"
            findings.append(Finding("PRIVACY_HISTORY_SCAN_FAILED", ".", detail, commit))
            continue
        for line in completed.stdout.decode(errors="replace").splitlines():
            prefix = f"{commit}:"
            payload = line[len(prefix):] if line.startswith(prefix) else line
            path_text = payload.split(":", 1)[0]
            if path_text in POLICY_EXCLUDED_PATHS or _signature_exempt(path_text):
                continue
            findings.append(
                Finding(
                    "PRIVACY_SECRET_HISTORY",
                    path_text,
                    "high-confidence secret signature exists in reachable history",
                    commit,
                )
            )
    return sorted(set(findings))


def audit_repository(root: Path, *, history: bool = False) -> list[Finding]:
    findings = scan_worktree(root)
    if history:
        findings.extend(scan_history(root))
    return sorted(set(findings))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root())
    parser.add_argument("--history", action="store_true")
    args = parser.parse_args(argv)
    findings = audit_repository(args.root.resolve(), history=args.history)
    if findings:
        for finding in findings:
            print(finding.render(), file=sys.stderr)
        print(f"FAIL: privacy audit reported {len(findings)} finding(s)", file=sys.stderr)
        return 2
    scope = "worktree and reachable history" if args.history else "worktree"
    print(f"PASS: privacy audit is clean for {scope}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
