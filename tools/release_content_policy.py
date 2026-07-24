#!/usr/bin/env python3
"""Pure, deterministic release-content classification and byte-scan rules.

This module is deliberately not an orchestrator.  It performs no filesystem,
Git, network, subprocess, or write operation.  Callers must establish regular
file identity, traverse a bounded candidate set, read bytes, and apply release
policy.  The functions here only classify caller-supplied paths and bytes.
"""

from __future__ import annotations

import sys

# Set this before importing any repository-local module.  This module currently
# has no local imports, but the invariant protects future reuse by audit CLIs.
sys.dont_write_bytecode = True

from dataclasses import dataclass
import hashlib
from pathlib import PurePosixPath
import re
from typing import Final


UNSAFE_PATH: Final = "unsafe-path"
CREDENTIAL_FILE: Final = "credential-file"
PRIVATE_KEY: Final = "private-key"
PROVIDER_TOKEN: Final = "provider-token"
CREDENTIAL_ASSIGNMENT: Final = "credential-assignment"
PRIVATE_HOME: Final = "private-home"
RESTRICTED_POTENTIAL_PATH: Final = "restricted-potential-path"
RESTRICTED_POTENTIAL_CONTENT: Final = "restricted-potential-content"
RUNTIME_ARTIFACT: Final = "runtime-artifact"
NESTED_ARCHIVE: Final = "nested-archive"
OPAQUE_BINARY_UNREVIEWED: Final = "opaque-binary-unreviewed"
CALCULATION_PAYLOAD_UNREVIEWED: Final = "calculation-payload-unreviewed"
FILE_SHA256_MISMATCH: Final = "file-sha256-mismatch"
SCAN_LIMIT_EXCEEDED: Final = "scan-limit-exceeded"

MAX_PATH_BYTES: Final = 4096
MAX_PATH_COMPONENT_BYTES: Final = 255
MAX_SCOPE_BYTES: Final = 96
MAX_SCAN_BYTES: Final = 8 * 1024 * 1024

ROLES: Final = frozenset(
    {
        "repository-source",
        "test-source",
        "schema",
        "structured-record",
        "canonical-pack-metadata",
        "official-document-body",
        "repository-public-asset",
        "synthetic-scientific-fixture",
        "calculation-payload",
        "opaque-binary",
    }
)
OFFICIAL_POLICIES: Final = frozenset(
    {
        "auto",
        "canonical-pack-metadata",
        "official-document-body",
    }
)

_RULE_IDS: Final = {
    UNSAFE_PATH: "RCP-PATH-001",
    CREDENTIAL_FILE: "RCP-PATH-002",
    PRIVATE_KEY: "RCP-CONTENT-001",
    PROVIDER_TOKEN: "RCP-CONTENT-002",
    CREDENTIAL_ASSIGNMENT: "RCP-CONTENT-003",
    PRIVATE_HOME: "RCP-CONTENT-004",
    RESTRICTED_POTENTIAL_PATH: "RCP-PATH-003",
    RESTRICTED_POTENTIAL_CONTENT: "RCP-CONTENT-005",
    RUNTIME_ARTIFACT: "RCP-PATH-004",
    NESTED_ARCHIVE: "RCP-PATH-005",
    OPAQUE_BINARY_UNREVIEWED: "RCP-CONTENT-006",
    CALCULATION_PAYLOAD_UNREVIEWED: "RCP-PATH-006",
    FILE_SHA256_MISMATCH: "RCP-INTEGRITY-001",
    SCAN_LIMIT_EXCEEDED: "RCP-BOUND-001",
}

_SCOPE_RE: Final = re.compile(r"[a-z][a-z0-9]*(?:[-.][a-z0-9]+)*\Z")
_SHA256_RE: Final = re.compile(r"[0-9a-f]{64}\Z")
_BLOB_OID_RE: Final = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")

_PRIVATE_KEY_BASENAMES: Final = frozenset(
    {
        "id_dsa",
        "id_ecdsa",
        "id_ed25519",
        "id_rsa",
        "private-key",
        "private_key",
    }
)
_CREDENTIAL_BASENAMES: Final = frozenset(
    {
        ".env",
        ".netrc",
        ".npmrc",
        ".pypirc",
        "auth.json",
        "credentials",
        "credentials.json",
        "credentials.yaml",
        "credentials.yml",
        "secrets",
        "secrets.json",
        "secrets.yaml",
        "secrets.yml",
    }
)
_CREDENTIAL_COMPONENTS: Final = frozenset({".aws", ".gnupg", ".ssh"})
_SAFE_ENV_TEMPLATES: Final = frozenset(
    {".env.example", ".env.sample", ".env.template"}
)
_RUNTIME_COMPONENTS: Final = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "private-runtime",
        "runtime",
        "runtime-data",
        "runtime-records",
        "venv",
    }
)
_RUNTIME_BASENAMES: Final = frozenset(
    {".coverage", ".ds_store", "coverage.xml"}
)
_RUNTIME_SUFFIXES: Final = (
    ".pyc",
    ".pyo",
    ".swp",
    ".swo",
    ".tmp",
)
_ARCHIVE_SUFFIXES: Final = (
    ".tar.gz",
    ".tar.bz2",
    ".tar.xz",
    ".tbz2",
    ".tgz",
    ".txz",
    ".7z",
    ".rar",
    ".tar",
    ".zip",
)
_OPAQUE_SUFFIXES: Final = (
    ".bin",
    ".bmp",
    ".class",
    ".dylib",
    ".exe",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".o",
    ".obj",
    ".pdf",
    ".png",
    ".pyc",
    ".so",
    ".tif",
    ".tiff",
    ".webp",
)
_CALCULATION_BASENAMES: Final = frozenset(
    {
        "chgcar",
        "contcar",
        "doscar",
        "eigenval",
        "ibzkpt",
        "locpot",
        "oszicar",
        "outcar",
        "pcdat",
        "procar",
        "report",
        "vasprun.xml",
        "wavecar",
        "waveder",
        "xdatcar",
    }
)
_SOURCE_SUFFIXES: Final = frozenset(
    {
        ".c",
        ".cc",
        ".cpp",
        ".css",
        ".f",
        ".f90",
        ".h",
        ".html",
        ".js",
        ".md",
        ".mplstyle",
        ".py",
        ".rst",
        ".sh",
        ".ts",
        ".tsx",
        ".txt",
    }
)
_STRUCTURED_SUFFIXES: Final = frozenset(
    {".csv", ".json", ".jsonl", ".toml", ".tsv", ".yaml", ".yml"}
)
_REPOSITORY_TEXT_BASENAMES: Final = frozenset(
    {
        ".dockerignore",
        ".editorconfig",
        ".gitattributes",
        ".gitignore",
        ".gitmodules",
        ".mailmap",
        ".npmignore",
        "codeowners",
    }
)
_PACK_METADATA_BASENAMES: Final = frozenset(
    {
        "corpus-manifest.json",
        "coverage.json",
        "license-review.json",
        "official-source-pack.json",
        "slice-manifest.json",
        "source-lock.json",
    }
)
_OFFICIAL_BODY_COMPONENTS: Final = frozenset(
    {"bodies", "body", "content", "documents", "sources"}
)
_PUBLIC_IMAGE_MAGICS: Final = {
    ".bmp": (b"BM",),
    ".gif": (b"GIF87a", b"GIF89a"),
    ".ico": (b"\x00\x00\x01\x00",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".jpg": (b"\xff\xd8\xff",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".tif": (b"II*\x00", b"MM\x00*"),
    ".tiff": (b"II*\x00", b"MM\x00*"),
    ".webp": (b"RIFF",),
}

_PROVIDER_TOKEN_PATTERNS: Final = (
    re.compile(rb"(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}(?![0-9A-Z])"),
    re.compile(rb"(?<![A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{20,}(?![A-Za-z0-9])"),
    re.compile(
        rb"(?<![A-Za-z0-9])github_pat_[A-Za-z0-9_]{22,}(?![A-Za-z0-9_])"
    ),
    re.compile(rb"(?<![A-Za-z0-9])sk-[A-Za-z0-9]{32,}(?![A-Za-z0-9])"),
)
_CREDENTIAL_ASSIGNMENT_RE: Final = re.compile(
    rb"""(?ix)
    (?<![A-Za-z0-9_])
    ["']?
    (?:
        password|passwd|
        api[_-]?key|
        access[_-]?token|
        auth(?:orization)?[_-]?token|
        secret(?:[_-]?key)?
    )
    ["']?
    [ \t]*[:=][ \t]*
    ["']?
    ([A-Za-z0-9._~+/=-]{16,})
    """
)
_PLACEHOLDER_FRAGMENTS: Final = (
    b"alice",
    b"changeme",
    b"example",
    b"placeholder",
    b"redacted",
    b"researcher",
    b"sample",
    b"user",
)
_PRIVATE_HOME_RE: Final = re.compile(
    rb"(?<![A-Za-z0-9._-])(?:/Users|/home)/"
    rb"([A-Za-z][A-Za-z0-9._-]{1,63})(?=/|(?:\r?\n)|\Z)"
)
_WINDOWS_PRIVATE_HOME_RE: Final = re.compile(
    rb"(?i)(?<![A-Za-z0-9._-])[A-Z]:\\Users\\"
    rb"([A-Za-z][A-Za-z0-9._-]{1,63})(?=\\|(?:\r?\n)|\Z)"
)
_SYNTHETIC_HOME_NAMES: Final = frozenset(
    {
        "alice",
        "demo",
        "example",
        "researcher",
        "runner",
        "shared",
        "test",
        "tester",
        "user",
        "username",
    }
)
_PRIVATE_KEY_BEGIN_RE: Final = re.compile(
    rb"(?m)^-----BEGIN ((?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY)-----[ \t]*\r?$"
)
_BASE64_LINE_RE: Final = re.compile(rb"[A-Za-z0-9+/=]{16,}\Z")

_VASP_TITEL_LINE: Final = re.compile(
    r"(?im)^[ \t]{0,16}TITEL[ \t]*=[ \t]*(?:PAW|US|NC)[^\r\n]*$"
)
_VASP_VRHFIN_LINE: Final = re.compile(
    r"(?im)^[ \t]{0,16}VRHFIN[ \t]*=[^\r\n]+$"
)
_VASP_POMASS_LINE: Final = re.compile(
    r"(?im)^[ \t]{0,16}POMASS[ \t]*=[^\r\n]+$"
)
_VASP_END_LINE: Final = re.compile(
    r"(?im)^[ \t]{0,16}End of Dataset[ \t]*$"
)
_VASP_HEADER_LINE: Final = re.compile(
    r"(?im)^[ \t]{0,16}(?:PAW|US|NC)(?:_PBE|_LDA)?[ \t]+[^\r\n]+$"
)
_PSCTR_HEADER_LINE: Final = re.compile(r"(?im)^[ \t]{0,16}PSCTR[ \t]*$")
_PSCTR_STRUCTURE_LINES: Final = (
    re.compile(r"(?im)^[ \t]{0,16}Atomic number[ \t]*:[^\r\n]+$"),
    re.compile(r"(?im)^[ \t]{0,16}Valence charge[ \t]*:[^\r\n]+$"),
    re.compile(
        r"(?im)^[ \t]{0,16}(?:Down|Up) pseudopotential follows[ \t]*$"
    ),
    re.compile(r"(?im)^[ \t]{0,16}Core corrections?[^\r\n]*$"),
)
_BINARY_MAGICS: Final = (
    b"\x00asm",
    b"\x1f\x8b",
    b"\x7fELF",
    b"BM",
    b"GIF87a",
    b"GIF89a",
    b"MZ",
    b"PK\x03\x04",
    b"%PDF-",
    b"\x89PNG\r\n\x1a\n",
)


@dataclass(frozen=True, order=True)
class Finding:
    """A sortable non-leaking rule result.

    Empty strings represent unavailable file identities for path-only scans.
    Keeping every field textual guarantees total ordering across both path and
    byte findings.
    """

    code: str
    severity: str
    scope: str
    role: str
    path: str
    path_sha256: str
    file_sha256: str
    blob_oid: str
    rule_id: str

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity,
            "scope": self.scope,
            "role": self.role,
            "path": self.path,
            "path_sha256": self.path_sha256,
            "file_sha256": self.file_sha256,
            "blob_oid": self.blob_oid,
            "rule_id": self.rule_id,
        }


def _path_bytes(path: str) -> bytes:
    return path.encode("utf-8", errors="surrogatepass")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _path_sha256(path: str) -> str:
    return _sha256(_path_bytes(path))


def _path_is_canonical(path: str) -> bool:
    if not isinstance(path, str) or not path:
        return False
    raw = _path_bytes(path)
    if len(raw) > MAX_PATH_BYTES or b"\x00" in raw or b"\\" in raw:
        return False
    if any(character in "\r\n\t" or not character.isprintable() for character in path):
        return False
    parsed = PurePosixPath(path)
    if parsed.is_absolute() or parsed.as_posix() != path:
        return False
    if any(
        part in {"", ".", ".."}
        or len(_path_bytes(part)) > MAX_PATH_COMPONENT_BYTES
        for part in parsed.parts
    ):
        return False
    return True


def _validate_role_scope(role: str, scope: str) -> None:
    if role not in ROLES:
        raise ValueError("role is not in the fixed release-content vocabulary")
    if (
        not isinstance(scope, str)
        or len(scope.encode("ascii", errors="ignore")) != len(scope)
        or len(scope) > MAX_SCOPE_BYTES
        or _SCOPE_RE.fullmatch(scope) is None
    ):
        raise ValueError("scope does not satisfy the fixed release-content grammar")


def _validate_file_identity(file_sha256: str, blob_oid: str | None) -> str:
    if not isinstance(file_sha256, str) or _SHA256_RE.fullmatch(file_sha256) is None:
        raise ValueError("file_sha256 must be a lowercase SHA-256 digest")
    normalized_oid = "" if blob_oid is None else blob_oid
    if (
        not isinstance(normalized_oid, str)
        or (
            normalized_oid
            and _BLOB_OID_RE.fullmatch(normalized_oid) is None
        )
    ):
        raise ValueError("blob_oid must be a lowercase SHA-1 or SHA-256 object id")
    return normalized_oid


def _provider_token_present(raw: bytes) -> bool:
    return any(pattern.search(raw) is not None for pattern in _PROVIDER_TOKEN_PATTERNS)


def _credential_assignments(raw: bytes) -> tuple[re.Match[bytes], ...]:
    matches: list[re.Match[bytes]] = []
    for match in _CREDENTIAL_ASSIGNMENT_RE.finditer(raw):
        candidate = match.group(1).lower()
        if any(fragment in candidate for fragment in _PLACEHOLDER_FRAGMENTS):
            continue
        if len(set(candidate)) <= 2:
            continue
        matches.append(match)
    return tuple(matches)


def _path_contains_secret(path: str) -> bool:
    raw = _path_bytes(path)
    return _provider_token_present(raw) or bool(_credential_assignments(raw))


def _display_path(path: str, *, canonical: bool) -> str:
    if not canonical:
        return "<unsafe-path>"
    if _path_contains_secret(path):
        return "<redacted-path>"
    return path


def _potential_path(path: str) -> bool:
    name = PurePosixPath(path).name.casefold()
    return name == "potcar" or name.startswith("potcar.") or name.endswith(".psctr")


def _credential_path(path: str) -> bool:
    parts = tuple(part.casefold() for part in PurePosixPath(path).parts)
    name = parts[-1]
    if any(part in _CREDENTIAL_COMPONENTS for part in parts):
        return True
    if name in _CREDENTIAL_BASENAMES:
        return True
    return (
        name.startswith(".env.")
        and name not in _SAFE_ENV_TEMPLATES
    )


def _private_key_path(path: str) -> bool:
    name = PurePosixPath(path).name.casefold()
    return (
        name in _PRIVATE_KEY_BASENAMES
        or name.startswith("id_rsa.")
        or name.startswith("id_ed25519.")
        or "private-key" in name
        or "private_key" in name
    )


def _runtime_path(path: str) -> bool:
    parts = tuple(part.casefold() for part in PurePosixPath(path).parts)
    name = parts[-1]
    return (
        any(part in _RUNTIME_COMPONENTS for part in parts)
        or name in _RUNTIME_BASENAMES
        or name.endswith(_RUNTIME_SUFFIXES)
    )


def _archive_path(path: str) -> bool:
    return PurePosixPath(path).name.casefold().endswith(_ARCHIVE_SUFFIXES)


def _calculation_path(path: str) -> bool:
    return PurePosixPath(path).name.casefold() in _CALCULATION_BASENAMES


def _opaque_path(path: str) -> bool:
    return PurePosixPath(path).name.casefold().endswith(_OPAQUE_SUFFIXES)


def _is_public_asset_path(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return (
        len(parts) >= 3
        and parts[:2] == ("docs", "images")
        and PurePosixPath(path).suffix in _PUBLIC_IMAGE_MAGICS
    )


def _public_image_magic_matches(path: str, raw: bytes) -> bool:
    if not _is_public_asset_path(path):
        return False
    suffix = PurePosixPath(path).suffix
    if suffix == ".webp":
        return (
            len(raw) >= 12
            and raw.startswith(b"RIFF")
            and raw[8:12] == b"WEBP"
        )
    return any(raw.startswith(magic) for magic in _PUBLIC_IMAGE_MAGICS[suffix])


def _is_synthetic_fixture_path(path: str) -> bool:
    exact_parts = PurePosixPath(path).parts
    if (
        len(exact_parts) >= 5
        and exact_parts[0] == "skills"
        and exact_parts[2:4] == ("references", "forward-fixtures")
        and exact_parts[-1].endswith(".sanitized.out")
    ):
        return True
    folded_parts = tuple(part.casefold() for part in exact_parts)
    return "fixtures" in folded_parts and any(
        part in {"scientific-fixtures", "synthetic", "synthetic-fixtures"}
        for part in folded_parts
    )


def _is_pack_path(path: str) -> bool:
    return "official-source-pack" in {
        part.casefold() for part in PurePosixPath(path).parts
    }


def _is_official_body_path(path: str) -> bool:
    parts = tuple(part.casefold() for part in PurePosixPath(path).parts)
    if len(parts) < 4 or parts[0] != "skills" or "references" not in parts:
        return False
    if "official-source-pack" in parts:
        pack_index = parts.index("official-source-pack")
        return any(
            part in _OFFICIAL_BODY_COMPONENTS
            for part in parts[pack_index + 1 : -1]
        )
    return any(part.startswith("official-") for part in parts[3:-1]) or (
        parts[-1].startswith("official-")
        and PurePosixPath(path).suffix.casefold() in _SOURCE_SUFFIXES.union(
            {".pdf"}
        )
    )


def _is_pack_metadata_path(path: str) -> bool:
    if not _is_pack_path(path):
        return False
    parts = tuple(part.casefold() for part in PurePosixPath(path).parts)
    pack_index = parts.index("official-source-pack")
    if any(
        part in _OFFICIAL_BODY_COMPONENTS
        for part in parts[pack_index + 1 : -1]
    ):
        return False
    name = parts[-1]
    return name in _PACK_METADATA_BASENAMES or name.endswith(
        (".json", ".yaml", ".yml")
    )


def classify_path(path: str, official_policy: str | None = None) -> str:
    """Classify one canonical repository-relative POSIX path.

    ``official_policy`` is a bounded classification assertion, never a waiver.
    It accepts only ``auto``, ``official-document-body``, or
    ``canonical-pack-metadata``; the latter two must agree with a recognized
    official-document path shape.
    """

    if not isinstance(path, str) or not _path_is_canonical(path):
        raise ValueError("path does not satisfy the fixed canonical POSIX grammar")
    assertion = "auto" if official_policy is None else official_policy
    if not isinstance(assertion, str) or assertion not in OFFICIAL_POLICIES:
        raise ValueError("official_policy is not in the fixed vocabulary")
    if assertion == "official-document-body":
        if not _is_official_body_path(path):
            raise ValueError("official body assertion does not match path grammar")
        return "official-document-body"
    if assertion == "canonical-pack-metadata":
        if not _is_pack_metadata_path(path):
            raise ValueError("official metadata assertion does not match path grammar")
        return "canonical-pack-metadata"

    if _is_official_body_path(path):
        return "official-document-body"
    if _is_pack_metadata_path(path):
        return "canonical-pack-metadata"
    if _is_synthetic_fixture_path(path):
        return "synthetic-scientific-fixture"
    if _is_public_asset_path(path):
        return "repository-public-asset"

    parts = tuple(part.casefold() for part in PurePosixPath(path).parts)
    name = parts[-1]
    suffix = PurePosixPath(name).suffix.casefold()
    if parts[0] == "tests" or name.startswith("test_"):
        return "test-source"
    if name.endswith(".schema.json") or parts[0] in {"schema", "schemas"}:
        return "schema"
    if _calculation_path(path) or _potential_path(path):
        return "calculation-payload"
    if suffix in _STRUCTURED_SUFFIXES:
        return "structured-record"
    if (
        suffix in _SOURCE_SUFFIXES
        or name in _REPOSITORY_TEXT_BASENAMES
        or name in {"makefile", "skill.md"}
    ):
        return "repository-source"
    return "opaque-binary"


def _make_finding(
    code: str,
    *,
    path: str,
    canonical_path: bool,
    role: str,
    scope: str,
    file_sha256: str,
    blob_oid: str,
) -> Finding:
    return Finding(
        code=code,
        severity="blocker",
        scope=scope,
        role=role,
        path=_display_path(path, canonical=canonical_path),
        path_sha256=_path_sha256(path),
        file_sha256=file_sha256,
        blob_oid=blob_oid,
        rule_id=_RULE_IDS[code],
    )


def _path_codes(path: str, role: str) -> frozenset[str]:
    codes: set[str] = set()
    if _private_key_path(path):
        codes.add(PRIVATE_KEY)
    elif _credential_path(path):
        codes.add(CREDENTIAL_FILE)
    if _provider_token_present(_path_bytes(path)):
        codes.add(PROVIDER_TOKEN)
    if _credential_assignments(_path_bytes(path)):
        codes.add(CREDENTIAL_ASSIGNMENT)
    if _potential_path(path):
        codes.add(RESTRICTED_POTENTIAL_PATH)
    if _runtime_path(path):
        codes.add(RUNTIME_ARTIFACT)
    if _archive_path(path):
        codes.add(NESTED_ARCHIVE)
    if (
        role == "calculation-payload"
        or (_calculation_path(path) and role != "synthetic-scientific-fixture")
    ):
        codes.add(CALCULATION_PAYLOAD_UNREVIEWED)
    if role == "repository-public-asset":
        if not _is_public_asset_path(path):
            codes.add(OPAQUE_BINARY_UNREVIEWED)
    elif role == "opaque-binary" or (
        _opaque_path(path)
        and role
        not in {"official-document-body", "synthetic-scientific-fixture"}
    ):
        codes.add(OPAQUE_BINARY_UNREVIEWED)
    return frozenset(codes)


def _scan_path(
    path: str,
    role: str,
    scope: str,
    *,
    file_sha256: str,
    blob_oid: str,
) -> tuple[Finding, ...]:
    canonical = isinstance(path, str) and _path_is_canonical(path)
    if not isinstance(path, str):
        raise TypeError("path must be text")
    codes = {UNSAFE_PATH} if not canonical else set(_path_codes(path, role))
    return tuple(
        sorted(
            _make_finding(
                code,
                path=path,
                canonical_path=canonical,
                role=role,
                scope=scope,
                file_sha256=file_sha256,
                blob_oid=blob_oid,
            )
            for code in codes
        )
    )


def scan_path(path: str, role: str, scope: str) -> tuple[Finding, ...]:
    """Apply path-only release rules to caller-supplied metadata."""

    _validate_role_scope(role, scope)
    return _scan_path(
        path,
        role,
        scope,
        file_sha256="",
        blob_oid="",
    )


def _has_private_key(raw: bytes) -> bool:
    for begin in _PRIVATE_KEY_BEGIN_RE.finditer(raw):
        key_type = begin.group(1)
        end_marker = b"-----END " + key_type + b"-----"
        end_index = raw.find(end_marker, begin.end(), begin.end() + 256 * 1024)
        if end_index < 0:
            continue
        body = raw[begin.end() : end_index]
        base64_bytes = sum(
            len(line.strip())
            for line in body.splitlines()
            if _BASE64_LINE_RE.fullmatch(line.strip()) is not None
        )
        if base64_bytes >= 32:
            return True
    return False


def _has_private_home(raw: bytes) -> bool:
    for pattern in (_PRIVATE_HOME_RE, _WINDOWS_PRIVATE_HOME_RE):
        for match in pattern.finditer(raw):
            try:
                name = match.group(1).decode("ascii").casefold()
            except UnicodeDecodeError:
                return True
            if name not in _SYNTHETIC_HOME_NAMES:
                return True
    return False


def _has_restricted_potential(raw: bytes) -> bool:
    text = raw.decode("utf-8", errors="replace")
    vasp_structures = sum(
        pattern.search(text) is not None
        for pattern in (
            _VASP_TITEL_LINE,
            _VASP_VRHFIN_LINE,
            _VASP_POMASS_LINE,
            _VASP_END_LINE,
            _VASP_HEADER_LINE,
        )
    )
    if vasp_structures >= 3 and (
        _VASP_TITEL_LINE.search(text) is not None
        or _VASP_VRHFIN_LINE.search(text) is not None
    ):
        return True
    psctr_structures = sum(
        pattern.search(text) is not None for pattern in _PSCTR_STRUCTURE_LINES
    )
    return (
        _PSCTR_HEADER_LINE.search(text) is not None
        and psctr_structures >= 2
    )


def _looks_binary(raw: bytes) -> bool:
    prefix = raw[:16]
    return b"\x00" in raw[:8192] or any(
        prefix.startswith(magic) for magic in _BINARY_MAGICS
    )


def scan_bytes(
    path: str,
    raw: bytes,
    role: str,
    scope: str,
    file_sha256: str,
    blob_oid: str | None = None,
) -> tuple[Finding, ...]:
    """Apply path, integrity, bound, and high-confidence byte rules.

    The caller-provided digest is authenticated against ``raw``.  Findings
    contain only stable metadata and hashes; matched bytes and context are never
    retained or returned.
    """

    _validate_role_scope(role, scope)
    if not isinstance(raw, bytes):
        raise TypeError("raw must be immutable bytes")
    normalized_oid = _validate_file_identity(file_sha256, blob_oid)
    path_findings = _scan_path(
        path,
        role,
        scope,
        file_sha256=file_sha256,
        blob_oid=normalized_oid,
    )
    canonical = isinstance(path, str) and _path_is_canonical(path)
    codes = {finding.code for finding in path_findings}
    if _sha256(raw) != file_sha256:
        codes.add(FILE_SHA256_MISMATCH)
    if len(raw) > MAX_SCAN_BYTES:
        codes.add(SCAN_LIMIT_EXCEEDED)
    else:
        if _has_private_key(raw):
            codes.add(PRIVATE_KEY)
        if _provider_token_present(raw):
            codes.add(PROVIDER_TOKEN)
        if _credential_assignments(raw):
            codes.add(CREDENTIAL_ASSIGNMENT)
        if _has_private_home(raw):
            codes.add(PRIVATE_HOME)
        if _has_restricted_potential(raw):
            codes.add(RESTRICTED_POTENTIAL_CONTENT)
        if role == "repository-public-asset":
            if not _public_image_magic_matches(path, raw):
                codes.add(OPAQUE_BINARY_UNREVIEWED)
        elif (
            role == "opaque-binary"
            or (
                _looks_binary(raw)
                and role
                not in {
                    "official-document-body",
                    "synthetic-scientific-fixture",
                }
            )
        ):
            codes.add(OPAQUE_BINARY_UNREVIEWED)
    return tuple(
        sorted(
            _make_finding(
                code,
                path=path,
                canonical_path=canonical,
                role=role,
                scope=scope,
                file_sha256=file_sha256,
                blob_oid=normalized_oid,
            )
            for code in codes
        )
    )


__all__ = [
    "CALCULATION_PAYLOAD_UNREVIEWED",
    "CREDENTIAL_ASSIGNMENT",
    "CREDENTIAL_FILE",
    "FILE_SHA256_MISMATCH",
    "Finding",
    "MAX_SCAN_BYTES",
    "NESTED_ARCHIVE",
    "OFFICIAL_POLICIES",
    "OPAQUE_BINARY_UNREVIEWED",
    "PRIVATE_HOME",
    "PRIVATE_KEY",
    "PROVIDER_TOKEN",
    "RESTRICTED_POTENTIAL_CONTENT",
    "RESTRICTED_POTENTIAL_PATH",
    "ROLES",
    "RUNTIME_ARTIFACT",
    "SCAN_LIMIT_EXCEEDED",
    "UNSAFE_PATH",
    "classify_path",
    "scan_bytes",
    "scan_path",
]
