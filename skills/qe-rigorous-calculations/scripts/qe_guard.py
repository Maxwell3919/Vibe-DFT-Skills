#!/usr/bin/env python3
"""Fail-closed planning, reference lookup, and audit gates for QE workflows.

The tool deliberately supports a narrow, deterministic pw.x input surface.  An
unsupported or unassessed condition blocks a positive conclusion instead of
being guessed by the caller.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import ssl
import subprocess
import tempfile
from typing import Any
import urllib.error
import urllib.request


TOOL_VERSION = "1.1.0"
REPORT_SCHEMA_VERSION = "1.0"
SKILL_ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_REFERENCES = SKILL_ROOT / "references"
REFERENCES = (
    Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    / "vibe-dft-skills"
    / "official-provider-mirrors"
    / "qe-rigorous-calculations"
    / "provider-root"
    / "references"
)
MANIFEST_PATH = (
    REPOSITORY_REFERENCES
    / "manual-cache-receipts"
    / "manifest.json"
)
PW_OFFICIAL_URL = "https://www.quantum-espresso.org/Doc/INPUT_PW.html"

NAMELIST_ORDER = ["control", "system", "electrons", "ions", "cell", "fcp", "rism"]
REQUIRED_NAMELISTS = ["control", "system", "electrons"]
CARD_NAMES = {
    "ATOMIC_SPECIES",
    "ATOMIC_POSITIONS",
    "K_POINTS",
    "ADDITIONAL_K_POINTS",
    "CELL_PARAMETERS",
    "CONSTRAINTS",
    "OCCUPATIONS",
    "ATOMIC_VELOCITIES",
    "ATOMIC_FORCES",
    "SOLVENTS",
    "HUBBARD",
}
AUTOMATED_NAMELIST_FIELDS = {
    "control": {
        "calculation",
        "title",
        "verbosity",
        "restart_mode",
        "prefix",
        "pseudo_dir",
        "outdir",
        "tprnfor",
        "tstress",
        "etot_conv_thr",
        "forc_conv_thr",
        "nstep",
        "max_seconds",
        "disk_io",
    },
    "system": {
        "ibrav",
        "nat",
        "ntyp",
        "ecutwfc",
        "ecutrho",
        "occupations",
        "smearing",
        "degauss",
        "nbnd",
        "space_group",
        "a",
        "b",
        "c",
        "cosab",
        "cosac",
        "cosbc",
        "lspinorb",
        "noncolin",
    },
    "electrons": {"conv_thr"},
    "ions": {"ion_dynamics"},
    "cell": {"cell_dynamics", "press", "press_conv_thr", "cell_dofree"},
}
AUTOMATED_CARDS = {"ATOMIC_SPECIES", "ATOMIC_POSITIONS", "K_POINTS", "CELL_PARAMETERS"}
PW_SOURCE = "https://www.quantum-espresso.org/Doc/INPUT_PW.html"
TASK_WORKFLOWS = {
    "scf": ["pw.x:scf"],
    "relax": ["pw.x:relax"],
    "vc-relax": ["pw.x:vc-relax"],
    "bands": ["pw.x:scf", "pw.x:bands", "bands.x"],
    "dos": ["pw.x:scf", "pw.x:nscf", "dos.x"],
    "pdos": ["pw.x:scf", "pw.x:nscf", "projwfc.x"],
    "phonon": ["pw.x:scf", "ph.x"],
    "epc": ["pw.x:scf", "ph.x:electron_phonon"],
    "neb": ["neb.x"],
}
PLAN_ALLOWED_CALCULATIONS = {
    "scf": {"scf"},
    "relax": {"relax"},
    "vc-relax": {"vc-relax"},
    "bands": {"scf", "bands"},
    "dos": {"scf", "nscf"},
    "pdos": {"scf", "nscf"},
    "phonon": {"scf"},
    "epc": {"scf"},
    "neb": set(),
}
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
CONVERGENCE_AUDIT_GATES = (
    "plan",
    "input_integrity",
    "pseudopotential_provenance",
    "official_version_match",
    "parent_ancestry",
    "runtime_paths",
    "execution_completion",
    "runtime_diagnostics",
)


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    message: str
    source: str | None = None

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }
        if self.source:
            result["official_source"] = self.source
        return result


def generated_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(payload: dict[str, Any], output: Path | None) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output is None:
        print(rendered, end="")
        return
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=output.parent, prefix=f".{output.name}.", delete=False
    ) as handle:
        handle.write(rendered)
        staged = Path(handle.name)
    os.replace(staged, output)


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not readable JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return value


def normalize_version(value: str) -> str:
    match = re.search(r"\d+(?:\.\d+)+(?:[-+._A-Za-z0-9]*)?", value)
    return match.group(0) if match else value.strip()


def strip_comment(line: str) -> str:
    quote: str | None = None
    result: list[str] = []
    for char in line:
        if quote:
            result.append(char)
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            result.append(char)
        elif char == "!":
            break
        else:
            result.append(char)
    return "".join(result)


def unquoted_slash(line: str) -> int | None:
    quote: str | None = None
    for index, char in enumerate(line):
        if quote:
            if char == quote:
                quote = None
        elif char in {"'", '"'}:
            quote = char
        elif char == "/":
            return index
    return None


def parse_namelists(text: str, findings: list[Finding]) -> tuple[dict[str, str], list[str], list[str]]:
    namelists: dict[str, str] = {}
    order: list[str] = []
    outside: list[str] = []
    current: str | None = None
    body: list[str] = []

    for line_number, raw in enumerate(text.splitlines(), start=1):
        clean = strip_comment(raw)
        if current is None:
            match = re.match(r"^\s*&([A-Za-z][A-Za-z0-9_]*)\b(.*)$", clean)
            if not match:
                outside.append(raw)
                continue
            current = match.group(1).lower()
            if current in namelists or current in order:
                findings.append(Finding("QE.INPUT.DUPLICATE_NAMELIST", "error", f"Duplicate &{current.upper()} namelist"))
            order.append(current)
            remainder = match.group(2)
            slash = unquoted_slash(remainder)
            if slash is not None:
                body.append(remainder[:slash])
                namelists[current] = "\n".join(body)
                current = None
                body = []
            else:
                body.append(remainder)
            continue

        slash = unquoted_slash(clean)
        if slash is None:
            body.append(clean)
        else:
            body.append(clean[:slash])
            assert current is not None
            namelists[current] = "\n".join(body)
            trailing = clean[slash + 1 :].strip()
            if trailing:
                findings.append(
                    Finding(
                        "QE.INPUT.TRAILING_AFTER_NAMELIST",
                        "error",
                        f"Unexpected content after &{current.upper()} terminator on line {line_number}",
                    )
                )
            current = None
            body = []

    if current is not None:
        findings.append(
            Finding("QE.INPUT.UNTERMINATED_NAMELIST", "error", f"&{current.upper()} has no '/' terminator")
        )
    return namelists, order, outside


def mask_quoted(text: str) -> str:
    quote: str | None = None
    result: list[str] = []
    for char in text:
        if quote:
            result.append(" ")
            if char == quote:
                quote = None
        elif char in {"'", '"'}:
            quote = char
            result.append(" ")
        else:
            result.append(char)
    return "".join(result)


def parse_assignments(body: str) -> dict[str, list[str]]:
    pattern = re.compile(r"(?i)(?<![A-Za-z0-9_])([A-Za-z][A-Za-z0-9_]*(?:\s*\([^)]*\))?)\s*=")
    masked = mask_quoted(body)
    matches = list(pattern.finditer(masked))
    assignments: dict[str, list[str]] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        key = re.sub(r"\s+", "", match.group(1)).lower()
        base = key.split("(", 1)[0]
        value = body[match.end() : end].strip(" \t\r\n,")
        assignments.setdefault(base, []).append(value)
    return assignments


def scalar(assignments: dict[str, list[str]], name: str) -> str | None:
    values = assignments.get(name.lower())
    if not values:
        return None
    value = values[-1].strip()
    if value.startswith(("'", '"')):
        quote = value[0]
        closing = value.find(quote, 1)
        return value[1:closing] if closing >= 0 else value[1:]
    token = re.match(r"[^,\s]+", value)
    return token.group(0) if token else value


def as_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def as_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value.replace("D", "E").replace("d", "e"))
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def as_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower().strip(".")
    if normalized in {"true", "t"}:
        return True
    if normalized in {"false", "f"}:
        return False
    return None


def parse_cards(lines: list[str], findings: list[Finding]) -> dict[str, dict[str, Any]]:
    cards: dict[str, dict[str, Any]] = {}
    current: str | None = None
    for raw in lines:
        clean = strip_comment(raw).strip()
        if not clean or clean.startswith("#"):
            continue
        token = clean.split(None, 1)[0].upper()
        if token in CARD_NAMES:
            if token not in AUTOMATED_CARDS:
                findings.append(
                    Finding("QE.INPUT.UNSUPPORTED_CARD", "error", f"{token} is outside the automated pw.x core")
                )
            if token in cards:
                findings.append(Finding("QE.INPUT.DUPLICATE_CARD", "error", f"Duplicate {token} card"))
            rest = clean[len(token) :].strip().strip("{}()").strip()
            option = rest.split()[0].lower() if rest else None
            cards[token] = {"option": option, "rows": []}
            current = token
        elif current is not None:
            cards[current]["rows"].append(clean)
        else:
            findings.append(Finding("QE.INPUT.UNPARSED_CONTENT", "error", f"Unrecognized content outside namelists: {clean}"))
    return cards


def add_required_positive(
    findings: list[Finding], assignments: dict[str, list[str]], name: str, kind: str = "float"
) -> float | int | None:
    value = scalar(assignments, name)
    if value is None:
        findings.append(
            Finding(f"QE.PW.REQUIRED.{name.upper()}", "error", f"{name} is required", PW_SOURCE)
        )
        return None
    parsed: float | int | None = as_int(value) if kind == "int" else as_float(value)
    if parsed is None or parsed <= 0:
        findings.append(
            Finding(f"QE.PW.INVALID.{name.upper()}", "error", f"{name} must be a positive {kind}", PW_SOURCE)
        )
        return None
    return parsed


def validate_k_points(card: dict[str, Any] | None, calculation: str, findings: list[Finding]) -> dict[str, Any]:
    summary: dict[str, Any] = {"mode": None, "count": None}
    if card is None:
        findings.append(Finding("QE.PW.MISSING.K_POINTS", "error", "K_POINTS card is required", PW_SOURCE))
        return summary
    mode = card["option"] or "tpiba"
    rows = card["rows"]
    summary["mode"] = mode
    allowed = {"tpiba", "automatic", "crystal", "gamma", "tpiba_b", "crystal_b", "tpiba_c", "crystal_c"}
    if mode not in allowed:
        findings.append(Finding("QE.PW.K_POINTS.MODE", "error", f"Unsupported K_POINTS mode: {mode}", PW_SOURCE))
        return summary
    if mode == "gamma":
        if rows:
            findings.append(Finding("QE.PW.K_POINTS.GAMMA_ROWS", "error", "K_POINTS gamma must have no data rows", PW_SOURCE))
        summary["count"] = 1
        return summary
    if mode == "automatic":
        if len(rows) != 1:
            findings.append(
                Finding("QE.PW.K_POINTS.AUTOMATIC_ROWS", "error", "K_POINTS automatic requires exactly one row", PW_SOURCE)
            )
            return summary
        fields = rows[0].split()
        try:
            values = [int(item) for item in fields]
        except ValueError:
            values = []
        if len(values) != 6 or any(value <= 0 for value in values[:3]) or any(value not in {0, 1} for value in values[3:]):
            findings.append(
                Finding(
                    "QE.PW.K_POINTS.AUTOMATIC_VALUES",
                    "error",
                    "Automatic mesh requires positive nk1..nk3 and offsets sk1..sk3 in {0,1}",
                    PW_SOURCE,
                )
            )
            return summary
        summary["mesh"] = values[:3]
        summary["offset"] = values[3:]
        summary["count"] = values[0] * values[1] * values[2]
        return summary
    if not rows:
        findings.append(Finding("QE.PW.K_POINTS.EXPLICIT_EMPTY", "error", f"K_POINTS {mode} has no nks row", PW_SOURCE))
        return summary
    try:
        nks = int(rows[0].split()[0])
    except (ValueError, IndexError):
        nks = 0
    if nks <= 0 or len(rows[1:]) != nks:
        findings.append(
            Finding(
                "QE.PW.K_POINTS.EXPLICIT_COUNT",
                "error",
                f"K_POINTS {mode} declares {nks} points but contains {len(rows[1:])} rows",
                PW_SOURCE,
            )
        )
        return summary
    for row in rows[1:]:
        fields = row.split()
        if len(fields) < 4 or any(as_float(item) is None for item in fields[:4]):
            findings.append(Finding("QE.PW.K_POINTS.EXPLICIT_VALUES", "error", "Each explicit k-point needs four numeric values", PW_SOURCE))
            break
    if mode.endswith("_c") and nks != 3:
        findings.append(Finding("QE.PW.K_POINTS.CONTOUR_COUNT", "error", f"K_POINTS {mode} requires nks=3", PW_SOURCE))
    if mode.endswith("_b") and calculation != "bands":
        findings.append(
            Finding("QE.PW.K_POINTS.BAND_MODE", "warning", f"K_POINTS {mode} is documented for band-structure plots", PW_SOURCE)
        )
    summary["count"] = nks
    return summary


def validate_pw_input(text: str) -> tuple[dict[str, Any], list[Finding]]:
    findings: list[Finding] = []
    if any(ord(char) > 127 for char in text):
        findings.append(Finding("QE.INPUT.NON_ASCII", "error", "pw.x input must use plain ASCII text", PW_SOURCE))
    if "\t" in text:
        findings.append(Finding("QE.INPUT.TAB", "error", "Tabs are rejected; use plain spaces", PW_SOURCE))
    if "\r" in text:
        findings.append(Finding("QE.INPUT.CRLF", "error", "CR/CRLF line endings are rejected", PW_SOURCE))

    namelists, order, outside = parse_namelists(text, findings)
    for name in REQUIRED_NAMELISTS:
        if name not in namelists:
            findings.append(
                Finding(f"QE.PW.MISSING_NAMELIST.{name.upper()}", "error", f"Missing &{name.upper()} namelist", PW_SOURCE)
            )
    order_positions = [NAMELIST_ORDER.index(name) for name in order if name in NAMELIST_ORDER]
    if order_positions != sorted(order_positions):
        findings.append(Finding("QE.PW.NAMELIST_ORDER", "error", "pw.x namelists are not in documented order", PW_SOURCE))

    assignments = {name: parse_assignments(body) for name, body in namelists.items()}
    for name in order:
        if name not in AUTOMATED_NAMELIST_FIELDS:
            findings.append(
                Finding("QE.INPUT.UNSUPPORTED_NAMELIST", "error", f"&{name.upper()} is outside the automated pw.x core")
            )
    for namelist, fields in assignments.items():
        allowed = AUTOMATED_NAMELIST_FIELDS.get(namelist, set())
        for field, values in fields.items():
            if field not in allowed:
                findings.append(
                    Finding(
                        "QE.INPUT.UNSUPPORTED_ASSIGNMENT",
                        "error",
                        f"&{namelist.upper()} field {field} is outside the automated pw.x core",
                    )
                )
            if len(values) > 1:
                findings.append(
                    Finding(
                        "QE.INPUT.DUPLICATE_ASSIGNMENT",
                        "error",
                        f"&{namelist.upper()} field {field} is assigned more than once",
                    )
                )
    control = assignments.get("control", {})
    system = assignments.get("system", {})
    electrons = assignments.get("electrons", {})
    calculation = (scalar(control, "calculation") or "scf").lower()
    allowed_calculations = {"scf", "nscf", "bands", "relax", "md", "vc-relax", "vc-md"}
    if calculation not in allowed_calculations:
        findings.append(Finding("QE.PW.CALCULATION", "error", f"Unsupported pw.x calculation: {calculation}", PW_SOURCE))
    restart_mode = (scalar(control, "restart_mode") or "from_scratch").lower()
    if restart_mode not in {"from_scratch", "restart"}:
        findings.append(Finding("QE.PW.RESTART_MODE", "error", "restart_mode must be from_scratch or restart", PW_SOURCE))

    for field in ["prefix", "outdir", "pseudo_dir"]:
        if scalar(control, field) is None:
            findings.append(
                Finding(
                    f"QE.POLICY.EXPLICIT_{field.upper()}",
                    "error",
                    f"Rigorous workflow requires explicit {field}; do not rely on its runtime default",
                    PW_SOURCE,
                )
            )
    conv_thr_value = scalar(electrons, "conv_thr")
    conv_thr = as_float(conv_thr_value)
    if conv_thr_value is None:
        findings.append(
            Finding(
                "QE.POLICY.EXPLICIT_CONV_THR",
                "error",
                "Rigorous workflow requires explicit conv_thr tied to the target observable",
                PW_SOURCE,
            )
        )
    elif conv_thr is None or conv_thr <= 0:
        findings.append(Finding("QE.PW.INVALID.CONV_THR", "error", "conv_thr must be positive", PW_SOURCE))

    has_space_group = scalar(system, "space_group") is not None
    ibrav_value = scalar(system, "ibrav")
    ibrav = as_int(ibrav_value)
    if ibrav_value is None and not has_space_group:
        findings.append(Finding("QE.PW.REQUIRED.IBRAV", "error", "ibrav is required unless space_group is set", PW_SOURCE))
    elif ibrav_value is not None and ibrav is None:
        findings.append(Finding("QE.PW.INVALID.IBRAV", "error", "ibrav must be an integer", PW_SOURCE))

    nat = add_required_positive(findings, system, "nat", "int")
    ntyp = add_required_positive(findings, system, "ntyp", "int")
    ecutwfc = add_required_positive(findings, system, "ecutwfc")
    ecutrho_value = scalar(system, "ecutrho")
    ecutrho = as_float(ecutrho_value)
    if ecutrho_value is None:
        findings.append(
            Finding(
                "QE.POLICY.EXPLICIT_ECUTRHO",
                "error",
                "Rigorous workflow requires explicit ecutrho; do not rely on the pseudopotential-dependent default",
                PW_SOURCE,
            )
        )
    elif ecutrho is None or ecutrho <= 0:
        findings.append(Finding("QE.PW.INVALID.ECUTRHO", "error", "ecutrho must be positive", PW_SOURCE))
    if ecutrho is not None and ecutwfc is not None and ecutrho < ecutwfc:
        findings.append(
            Finding("QE.PW.ECUTRHO_BELOW_ECUTWFC", "warning", "ecutrho is below ecutwfc; numerical adequacy is not established", PW_SOURCE)
        )
    nbnd_value = scalar(system, "nbnd")
    if nbnd_value is not None and (as_int(nbnd_value) is None or as_int(nbnd_value) <= 0):
        findings.append(Finding("QE.PW.INVALID.NBND", "error", "nbnd must be a positive integer", PW_SOURCE))
    space_group_value = scalar(system, "space_group")
    if space_group_value is not None and (
        as_int(space_group_value) is None or not 1 <= int(space_group_value) <= 230
    ):
        findings.append(Finding("QE.PW.INVALID.SPACE_GROUP", "error", "space_group must be an integer from 1 to 230", PW_SOURCE))
    for field in ["a", "b", "c"]:
        value = scalar(system, field)
        if value is not None and (as_float(value) is None or as_float(value) <= 0):
            findings.append(Finding("QE.PW.INVALID.LATTICE_PARAMETER", "error", f"{field.upper()} must be positive", PW_SOURCE))
    for field in ["cosab", "cosac", "cosbc"]:
        value = scalar(system, field)
        parsed = as_float(value)
        if value is not None and (parsed is None or not -1.0 < parsed < 1.0):
            findings.append(Finding("QE.PW.INVALID.LATTICE_COSINE", "error", f"{field} must lie strictly between -1 and 1", PW_SOURCE))

    celldm_present = "celldm" in system
    abc_present = any(name in system for name in ["a", "b", "c", "cosab", "cosac", "cosbc"])
    if celldm_present and abc_present:
        findings.append(Finding("QE.PW.LATTICE_MIXED_PARAMETERIZATION", "error", "Do not mix celldm and A/B/C/cos* lattice parameterizations", PW_SOURCE))

    cards = parse_cards(outside, findings)
    cell_card = cards.get("CELL_PARAMETERS")
    if ibrav == 0:
        if cell_card is None:
            findings.append(Finding("QE.PW.MISSING.CELL_PARAMETERS", "error", "CELL_PARAMETERS is required when ibrav=0", PW_SOURCE))
        else:
            if cell_card["option"] not in {"alat", "bohr", "angstrom"}:
                findings.append(
                    Finding("QE.POLICY.EXPLICIT_CELL_UNITS", "error", "CELL_PARAMETERS must state alat, bohr, or angstrom explicitly", PW_SOURCE)
                )
            if len(cell_card["rows"]) != 3 or any(
                len(row.split()) != 3 or any(as_float(item) is None for item in row.split())
                for row in cell_card["rows"]
            ):
                findings.append(Finding("QE.PW.CELL_PARAMETERS_VALUES", "error", "CELL_PARAMETERS requires exactly three numeric 3-vectors", PW_SOURCE))
    elif ibrav is not None:
        if cell_card is not None:
            findings.append(Finding("QE.PW.FORBIDDEN.CELL_PARAMETERS", "error", "CELL_PARAMETERS must be absent when ibrav is nonzero", PW_SOURCE))
        if not celldm_present and not abc_present:
            findings.append(Finding("QE.PW.MISSING_LATTICE_SCALE", "error", "Nonzero ibrav requires its documented lattice parameters", PW_SOURCE))

    species_card = cards.get("ATOMIC_SPECIES")
    species: list[dict[str, Any]] = []
    species_labels: set[str] = set()
    if species_card is None:
        findings.append(Finding("QE.PW.MISSING.ATOMIC_SPECIES", "error", "ATOMIC_SPECIES card is required", PW_SOURCE))
    else:
        rows = species_card["rows"]
        if ntyp is not None and len(rows) != ntyp:
            findings.append(
                Finding("QE.PW.ATOMIC_SPECIES_COUNT", "error", f"ntyp={ntyp} but ATOMIC_SPECIES contains {len(rows)} rows", PW_SOURCE)
            )
        for row in rows:
            fields = row.split()
            if len(fields) != 3 or as_float(fields[1]) is None or as_float(fields[1]) <= 0:
                findings.append(Finding("QE.PW.ATOMIC_SPECIES_ROW", "error", f"Invalid ATOMIC_SPECIES row: {row}", PW_SOURCE))
                continue
            label, _, pseudo = fields
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,31}", label):
                findings.append(Finding("QE.PW.ATOMIC_SPECIES_LABEL", "error", f"Unsupported species label: {label}", PW_SOURCE))
            if label in species_labels:
                findings.append(Finding("QE.PW.DUPLICATE_SPECIES_LABEL", "error", f"Duplicate species label: {label}", PW_SOURCE))
            if Path(pseudo).is_absolute() or ".." in Path(pseudo).parts:
                findings.append(Finding("QE.PW.UNSAFE_PSEUDO_NAME", "error", f"Pseudopotential must be a safe relative filename: {pseudo}", PW_SOURCE))
            species_labels.add(label)
            species.append({"label": label, "pseudopotential": pseudo})

    positions = cards.get("ATOMIC_POSITIONS")
    if positions is None:
        findings.append(Finding("QE.PW.MISSING.ATOMIC_POSITIONS", "error", "ATOMIC_POSITIONS card is required", PW_SOURCE))
    else:
        mode = positions["option"]
        if mode not in {"alat", "bohr", "angstrom", "crystal", "crystal_sg"}:
            findings.append(
                Finding("QE.POLICY.EXPLICIT_POSITION_UNITS", "error", "ATOMIC_POSITIONS must state units/mode explicitly", PW_SOURCE)
            )
        rows = positions["rows"]
        if nat is not None and len(rows) != nat:
            findings.append(
                Finding("QE.PW.ATOMIC_POSITIONS_COUNT", "error", f"nat={nat} but ATOMIC_POSITIONS contains {len(rows)} rows", PW_SOURCE)
            )
        for row in rows:
            fields = row.split()
            if not fields or fields[0] not in species_labels:
                findings.append(Finding("QE.PW.ATOMIC_POSITION_LABEL", "error", f"Position label is absent from ATOMIC_SPECIES: {row}", PW_SOURCE))
                continue
            if mode == "crystal_sg":
                if len(fields) < 2:
                    findings.append(Finding("QE.PW.ATOMIC_POSITION_ROW", "error", f"Invalid crystal_sg position row: {row}", PW_SOURCE))
                continue
            if len(fields) not in {4, 7} or any(as_float(item) is None for item in fields[1:4]):
                findings.append(Finding("QE.PW.ATOMIC_POSITION_ROW", "error", f"Invalid ATOMIC_POSITIONS row: {row}", PW_SOURCE))
            if len(fields) == 7 and any(item not in {"0", "1"} for item in fields[4:]):
                findings.append(Finding("QE.PW.ATOMIC_POSITION_FLAGS", "error", f"if_pos flags must be 0 or 1: {row}", PW_SOURCE))

    k_summary = validate_k_points(cards.get("K_POINTS"), calculation, findings)
    occupations = (scalar(system, "occupations") or "").lower()
    allowed_occupations = {"fixed", "smearing", "tetrahedra", "tetrahedra_lin", "tetrahedra_opt", "from_input"}
    if occupations not in allowed_occupations:
        findings.append(
            Finding("QE.PW.OCCUPATIONS", "error", "occupations must be explicit and supported by the automated core", PW_SOURCE)
        )
    degauss = as_float(scalar(system, "degauss"))
    if occupations == "smearing":
        if degauss is None or degauss <= 0:
            findings.append(Finding("QE.PW.SMEARING_DEGAUSS", "error", "occupations='smearing' requires a positive degauss", PW_SOURCE))
        if scalar(system, "smearing") is None:
            findings.append(Finding("QE.POLICY.EXPLICIT_SMEARING", "error", "occupations='smearing' requires an explicit smearing method", PW_SOURCE))
    elif scalar(system, "degauss") is not None or scalar(system, "smearing") is not None:
        findings.append(Finding("QE.PW.INACTIVE_SMEARING_FIELDS", "error", "smearing/degauss must be absent unless occupations='smearing'", PW_SOURCE))
    if occupations.startswith("tetrahedra") and k_summary.get("mode") != "automatic":
        findings.append(Finding("QE.PW.TETRAHEDRA_K_POINTS", "error", "Tetrahedron occupations require an automatic uniform k-point grid", PW_SOURCE))
    if occupations == "from_input":
        if "OCCUPATIONS" not in cards or scalar(system, "nbnd") is None or k_summary.get("count") != 1:
            findings.append(
                Finding("QE.PW.FROM_INPUT_PREREQUISITES", "error", "occupations='from_input' requires OCCUPATIONS, nbnd, and a single k-point", PW_SOURCE)
            )

    if as_bool(scalar(system, "lspinorb")) is True and as_bool(scalar(system, "noncolin")) is not True:
        findings.append(Finding("QE.PW.SOC_REQUIRES_NONCOLIN", "error", "lspinorb=.true. requires an explicit noncolin=.true. workflow", PW_SOURCE))
    for field in ["lspinorb", "noncolin"]:
        value = scalar(system, field)
        if value is not None and as_bool(value) is None:
            findings.append(Finding("QE.PW.INVALID_BOOLEAN", "error", f"{field} must be a Fortran boolean", PW_SOURCE))

    if calculation in {"relax", "vc-relax"}:
        ion_dynamics = scalar(assignments.get("ions", {}), "ion_dynamics")
        if ion_dynamics is None:
            findings.append(
                Finding("QE.POLICY.EXPLICIT_ION_DYNAMICS", "error", f"{calculation} requires explicit ion_dynamics", PW_SOURCE)
            )
        else:
            allowed_ion_dynamics = {"bfgs", "damp", "fire"} if calculation == "relax" else {"bfgs", "damp"}
            if ion_dynamics.lower() not in allowed_ion_dynamics:
                findings.append(
                    Finding("QE.PW.ION_DYNAMICS", "error", f"Unsupported ion_dynamics for {calculation}", PW_SOURCE)
                )
        for field in ["etot_conv_thr", "forc_conv_thr"]:
            if scalar(control, field) is None:
                findings.append(
                    Finding(f"QE.POLICY.EXPLICIT_{field.upper()}", "error", f"{calculation} requires explicit {field} acceptance control", PW_SOURCE)
                )
    if calculation == "vc-relax":
        if scalar(assignments.get("cell", {}), "press_conv_thr") is None:
            findings.append(
                Finding("QE.POLICY.EXPLICIT_PRESS_CONV_THR", "error", "vc-relax requires explicit press_conv_thr acceptance control", PW_SOURCE)
            )
        cell_dynamics = scalar(assignments.get("cell", {}), "cell_dynamics")
        if cell_dynamics is None:
            findings.append(
                Finding("QE.POLICY.EXPLICIT_CELL_DYNAMICS", "error", "vc-relax requires explicit cell_dynamics", PW_SOURCE)
            )
        elif cell_dynamics.lower() not in {"bfgs", "damp-pr", "damp-w"}:
            findings.append(Finding("QE.PW.CELL_DYNAMICS", "error", "Unsupported cell_dynamics for vc-relax", PW_SOURCE))
        ion_dynamics = (scalar(assignments.get("ions", {}), "ion_dynamics") or "").lower()
        if (ion_dynamics == "bfgs") != ((cell_dynamics or "").lower() == "bfgs"):
            findings.append(
                Finding("QE.PW.COUPLED_DYNAMICS", "error", "vc-relax requires ion_dynamics and cell_dynamics to use bfgs together", PW_SOURCE)
            )

    summary = {
        "executable": "pw.x",
        "calculation": calculation,
        "ibrav": ibrav,
        "nat": nat,
        "ntyp": ntyp,
        "ecutwfc_ry": ecutwfc,
        "ecutrho_ry": ecutrho,
        "conv_thr_ry": conv_thr,
        "degauss_ry": degauss,
        "occupations": occupations,
        "k_points": k_summary,
        "species": species,
        "prefix_explicit": scalar(control, "prefix") is not None,
        "outdir_explicit": scalar(control, "outdir") is not None,
        "pseudo_dir_explicit": scalar(control, "pseudo_dir") is not None,
        "_prefix_value": scalar(control, "prefix"),
        "_outdir_value": scalar(control, "outdir"),
        "_pseudo_dir_value": scalar(control, "pseudo_dir"),
        "restart_mode": restart_mode,
        "spin_orbit": as_bool(scalar(system, "lspinorb")) is True,
    }
    return summary, findings


def gate_status(findings: list[Finding], prefixes: tuple[str, ...]) -> str:
    selected = [item for item in findings if item.code.startswith(prefixes)]
    return "fail" if any(item.severity == "error" for item in selected) else "pass"


def validate_plan(plan: dict[str, Any], calculation: str, expected_version: str, findings: list[Finding]) -> str:
    required = [
        "schema_version",
        "case_id",
        "scientific_protocol_id",
        "task_type",
        "qe_version",
        "objective",
        "observable",
        "minimum_workflow",
    ]
    missing = [name for name in required if name not in plan]
    if missing:
        findings.append(Finding("QE.PLAN.MISSING_FIELDS", "error", f"Plan is missing: {', '.join(missing)}"))
        return "fail"
    if plan.get("schema_version") != REPORT_SCHEMA_VERSION:
        findings.append(Finding("QE.PLAN.SCHEMA_VERSION", "error", "Unsupported plan schema_version"))
    provenance = plan.get("provenance")
    if (
        plan.get("decision") != "pass"
        or not isinstance(provenance, dict)
        or provenance.get("collector") != "qe_guard"
        or provenance.get("collector_version") != TOOL_VERSION
    ):
        findings.append(Finding("QE.PLAN.PROVENANCE", "error", "Plan was not produced by the current qe_guard"))
    for field in ["case_id", "scientific_protocol_id"]:
        value = plan.get(field)
        if not isinstance(value, str) or not ID_RE.fullmatch(value):
            findings.append(Finding("QE.PLAN.IDENTIFIER", "error", f"Plan {field} is not a safe anonymous identifier"))
    if not isinstance(plan.get("objective"), str) or not plan["objective"].strip():
        findings.append(Finding("QE.PLAN.OBJECTIVE", "error", "Plan objective must be nonempty"))
    task = str(plan["task_type"])
    if task not in PLAN_ALLOWED_CALCULATIONS:
        findings.append(Finding("QE.PLAN.TASK_TYPE", "error", f"Unsupported plan task_type: {task}"))
    elif calculation not in PLAN_ALLOWED_CALCULATIONS[task]:
        findings.append(
            Finding("QE.PLAN.CALCULATION_MISMATCH", "error", f"pw.x calculation={calculation} is not a valid stage for plan task_type={task}")
        )
    elif plan.get("minimum_workflow") != TASK_WORKFLOWS[task]:
        findings.append(Finding("QE.PLAN.MINIMUM_WORKFLOW", "error", "Plan minimum_workflow differs from the deterministic task baseline"))
    if normalize_version(str(plan["qe_version"])) != normalize_version(expected_version):
        findings.append(Finding("QE.PLAN.VERSION_MISMATCH", "error", "Plan QE version differs from --expected-version"))
    observable = plan.get("observable")
    if not isinstance(observable, dict) or not observable.get("name") or not observable.get("unit"):
        findings.append(Finding("QE.PLAN.OBSERVABLE", "error", "Plan observable requires name and unit"))
    else:
        tolerances = [observable.get("absolute_tolerance"), observable.get("relative_tolerance")]
        if all(value is None for value in tolerances):
            findings.append(Finding("QE.PLAN.TOLERANCE", "error", "Plan requires an absolute or relative tolerance"))
        for value in tolerances:
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
            ):
                findings.append(Finding("QE.PLAN.TOLERANCE", "error", "Plan tolerances must be finite nonnegative numbers"))
    return gate_status(findings, ("QE.PLAN.",))


def validate_parent_manifest(
    parent: dict[str, Any] | None,
    calculation: str,
    restart_mode: str,
    expected_version: str,
    plan: dict[str, Any] | None,
    prefix: str | None,
    findings: list[Finding],
) -> str:
    needs_scientific_parent = calculation in {"nscf", "bands"}
    needs_restart_parent = restart_mode == "restart"
    if not needs_scientific_parent and not needs_restart_parent:
        return "pass"
    if parent is None:
        reason = "nscf/bands ancestry" if needs_scientific_parent else "restart lineage"
        findings.append(Finding("QE.ANCESTRY.MISSING", "error", f"A parent run manifest is required for {reason}"))
        return "fail"
    required = {
        "schema_version",
        "record_id",
        "code",
        "code_version",
        "task_type",
        "case_id",
        "scientific_protocol_id",
        "status",
        "scientific_acceptance",
        "configuration",
        "metrics",
        "evidence",
        "limitations",
        "provenance",
    }
    missing = sorted(required - set(parent))
    if missing:
        findings.append(Finding("QE.ANCESTRY.MANIFEST_FIELDS", "error", f"Parent manifest is missing: {', '.join(missing)}"))
    if parent.get("schema_version") != "1.0":
        findings.append(Finding("QE.ANCESTRY.MANIFEST_SCHEMA", "error", "Parent manifest schema_version must be 1.0"))
    if not isinstance(parent.get("record_id"), str) or not ID_RE.fullmatch(parent["record_id"]):
        findings.append(Finding("QE.ANCESTRY.RECORD_ID", "error", "Parent record_id is invalid"))
    if not isinstance(parent.get("metrics"), dict) or not isinstance(parent.get("limitations"), list):
        findings.append(Finding("QE.ANCESTRY.MANIFEST_STRUCTURE", "error", "Parent metrics/limitations have invalid types"))
    provenance = parent.get("provenance")
    if not isinstance(provenance, dict) or not all(
        isinstance(provenance.get(field), str) and provenance[field]
        for field in ["collector", "collector_version", "generated_utc"]
    ):
        findings.append(Finding("QE.ANCESTRY.PROVENANCE", "error", "Parent manifest provenance is incomplete"))
    if parent.get("code") != "qe":
        findings.append(Finding("QE.ANCESTRY.CODE", "error", "Parent manifest code must be qe"))
    if normalize_version(str(parent.get("code_version", ""))) != normalize_version(expected_version):
        findings.append(Finding("QE.ANCESTRY.VERSION", "error", "Parent manifest QE version differs from the planned executable"))
    parent_status = parent.get("status")
    parent_acceptance = parent.get("scientific_acceptance")
    if (
        parent_status not in {"planned", "running", "completed", "stopped", "failed"}
        or parent_acceptance not in {"not_assessed", "requires_human_review"}
        or (parent_status != "completed" and parent_acceptance != "not_assessed")
    ):
        findings.append(
            Finding(
                "QE.ANCESTRY.STATE",
                "error",
                "Parent run state must follow the immutable pre-decision run-manifest contract",
            )
        )
    if plan is not None:
        if parent.get("case_id") != plan.get("case_id"):
            findings.append(Finding("QE.ANCESTRY.CASE", "error", "Parent and plan case_id values differ"))
        if parent.get("scientific_protocol_id") != plan.get("scientific_protocol_id"):
            findings.append(Finding("QE.ANCESTRY.PROTOCOL", "error", "Parent and plan protocol ids differ"))
    configuration = parent.get("configuration")
    if not isinstance(configuration, dict) or configuration.get("prefix") != prefix:
        findings.append(
            Finding("QE.ANCESTRY.PREFIX", "error", "Parent configuration must bind the same privacy-safe prefix")
        )
    evidence = parent.get("evidence")
    evidence = evidence if isinstance(evidence, list) else []
    if any(
        not isinstance(item, dict)
        or not isinstance(item.get("role"), str)
        or not isinstance(item.get("label"), str)
        or item.get("status") not in {"present", "missing", "redacted", "external"}
        or (
            item.get("status") == "present"
            and not (
                isinstance(item.get("sha256"), str)
                and re.fullmatch(r"[a-f0-9]{64}", item["sha256"])
            )
        )
        or (item.get("status") == "missing" and item.get("sha256") is not None)
        for item in evidence
    ):
        findings.append(Finding("QE.ANCESTRY.EVIDENCE_SCHEMA", "error", "Parent evidence entries do not match the run-manifest contract"))
    present_roles = {
        item.get("role")
        for item in evidence
        if isinstance(item, dict)
        and item.get("status") == "present"
        and isinstance(item.get("sha256"), str)
        and re.fullmatch(r"[a-f0-9]{64}", item["sha256"])
    }
    if needs_scientific_parent:
        if parent_status != "completed":
            findings.append(
                Finding(
                    "QE.ANCESTRY.SCIENTIFIC_PARENT_NOT_COMPLETED",
                    "error",
                    "nscf/bands requires a technically completed parent run",
                )
            )
        findings.append(
            Finding(
                "QE.ANCESTRY.DECISION_BUNDLE_REQUIRED",
                "error",
                "nscf/bands scientific ancestry requires an externally trusted bundle containing the calculation record, human scientific decision, and post-decision claim map; this CLI has no platform human-trust resolver",
            )
        )
        if parent.get("task_type") not in {"scf", "static"}:
            findings.append(Finding("QE.ANCESTRY.TASK", "error", "nscf/bands parent must be an SCF/static run"))
        if not present_roles.intersection({"charge_density", "scf_density", "save_directory"}):
            findings.append(
                Finding(
                    "QE.ANCESTRY.DENSITY_EVIDENCE",
                    "error",
                    "Parent manifest lacks hashed charge-density/save-directory evidence",
                )
            )
    if needs_restart_parent:
        if parent_status != "completed":
            findings.append(
                Finding(
                    "QE.ANCESTRY.RESTART_PARENT_NOT_COMPLETED",
                    "error",
                    "A restart requires a technically completed parent run",
                )
            )
        if not present_roles.intersection({"restart_checkpoint", "save_directory"}):
            findings.append(
                Finding("QE.ANCESTRY.RESTART_EVIDENCE", "error", "Restart manifest lacks hashed checkpoint/save-directory evidence")
            )
    return gate_status(findings, ("QE.ANCESTRY.",))


def validate_pseudopotentials(
    species: list[dict[str, Any]],
    pseudo_dir: Path | None,
    pseudo_manifest_path: Path | None,
    require_spin_orbit: bool,
    findings: list[Finding],
) -> tuple[str, list[dict[str, Any]]]:
    if pseudo_dir is None:
        findings.append(
            Finding("QE.PSEUDO.NOT_ASSESSED", "incomplete", "Provide --pseudo-dir to verify pseudopotential presence and hashes")
        )
        return "incomplete", []
    if not pseudo_dir.is_dir():
        findings.append(Finding("QE.PSEUDO.DIRECTORY", "error", "The supplied pseudopotential directory is unavailable"))
        return "fail", []
    manifest_entries: list[dict[str, Any]] = []
    if pseudo_manifest_path is None:
        findings.append(
            Finding(
                "QE.PSEUDO.MANIFEST_NOT_ASSESSED",
                "incomplete",
                "Provide --pseudo-manifest to bind expected hashes and declared sources",
            )
        )
    else:
        try:
            manifest = load_json(pseudo_manifest_path, "pseudopotential manifest")
        except ValueError as exc:
            findings.append(Finding("QE.PSEUDO.MANIFEST_INVALID", "error", str(exc)))
        else:
            raw_entries = manifest.get("pseudopotentials")
            if manifest.get("schema_version") != "1.0" or not isinstance(raw_entries, list):
                findings.append(
                    Finding(
                        "QE.PSEUDO.MANIFEST_SCHEMA",
                        "error",
                        "Pseudopotential manifest requires schema_version 1.0 and a pseudopotentials list",
                    )
                )
            else:
                manifest_entries = [item for item in raw_entries if isinstance(item, dict)]
                if len(manifest_entries) != len(raw_entries):
                    findings.append(Finding("QE.PSEUDO.MANIFEST_ENTRY", "error", "Every manifest entry must be an object"))
    expected_names = {item["pseudopotential"] for item in species}
    declared_names = [item.get("filename") for item in manifest_entries]
    if manifest_entries and (set(declared_names) != expected_names or len(set(declared_names)) != len(declared_names)):
        findings.append(
            Finding("QE.PSEUDO.MANIFEST_COVERAGE", "error", "Manifest filenames must exactly cover this input without duplicates")
        )
    manifest_by_name = {
        str(item.get("filename")): item
        for item in manifest_entries
        if isinstance(item.get("filename"), str)
    }
    evidence: list[dict[str, Any]] = []
    functionals: set[str] = set()
    root = pseudo_dir.resolve()
    for item in species:
        name = item["pseudopotential"]
        candidate = (root / name).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            findings.append(Finding("QE.PSEUDO.PATH_ESCAPE", "error", f"Pseudopotential escapes --pseudo-dir: {name}"))
            continue
        if not candidate.is_file() or candidate.stat().st_size == 0:
            findings.append(Finding("QE.PSEUDO.MISSING", "error", f"Missing or empty pseudopotential: {name}"))
            continue
        actual_sha = sha256_file(candidate)
        declaration = manifest_by_name.get(name)
        if declaration is None and pseudo_manifest_path is not None:
            findings.append(Finding("QE.PSEUDO.MANIFEST_MISSING_FILE", "error", f"Manifest has no declaration for {name}"))
        elif declaration is not None:
            declared_sha = declaration.get("sha256")
            source = declaration.get("source")
            source_url = declaration.get("source_url")
            if not isinstance(declared_sha, str) or not SHA256_RE.fullmatch(declared_sha) or declared_sha != actual_sha:
                findings.append(Finding("QE.PSEUDO.MANIFEST_HASH", "error", f"Manifest hash does not match {name}"))
            if not isinstance(source, str) or not source.strip():
                findings.append(Finding("QE.PSEUDO.MANIFEST_SOURCE", "error", f"Manifest source is missing for {name}"))
            if not isinstance(source_url, str) or not re.fullmatch(r"https://[^\s]+", source_url):
                findings.append(Finding("QE.PSEUDO.MANIFEST_SOURCE_URL", "error", f"Manifest requires an HTTPS source URL for {name}"))
        header_text = candidate.read_bytes()[: 256 * 1024].decode("utf-8", errors="replace")
        upf_signature = "<UPF" in header_text or "<PP_HEADER" in header_text
        if not upf_signature:
            findings.append(
                Finding("QE.PSEUDO.UNRECOGNIZED_FORMAT", "error", f"No UPF signature found in {name}", PW_SOURCE)
            )
        header_match = re.search(r"<PP_HEADER\b([^>]*)>", header_text, flags=re.I | re.S)
        attributes: dict[str, str] = {}
        if header_match:
            attributes = {
                key.lower(): value.strip()
                for key, _, value in re.findall(
                    r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(['\"])(.*?)\2",
                    header_match.group(1),
                    flags=re.S,
                )
            }
        functional = attributes.get("functional")
        relativistic = attributes.get("relativistic")
        has_so = as_bool(attributes.get("has_so"))
        if functional:
            functionals.add(functional.lower())
        else:
            findings.append(
                Finding("QE.PSEUDO.FUNCTIONAL_UNKNOWN", "incomplete", f"Functional metadata was not found in {name}")
            )
        if declaration is not None:
            declared_functional = declaration.get("xc_functional")
            declared_relativistic = declaration.get("relativistic")
            if not isinstance(declared_functional, str) or not functional or declared_functional.lower() != functional.lower():
                findings.append(Finding("QE.PSEUDO.MANIFEST_XC", "error", f"Manifest XC does not match UPF metadata for {name}"))
            if (
                not isinstance(declared_relativistic, str)
                or not relativistic
                or declared_relativistic.lower() != relativistic.lower()
            ):
                findings.append(
                    Finding("QE.PSEUDO.MANIFEST_RELATIVISTIC", "error", f"Manifest relativistic mode does not match UPF metadata for {name}")
                )
        if require_spin_orbit:
            fully_relativistic = relativistic is not None and "full" in relativistic.lower()
            if has_so is False or (relativistic is not None and not fully_relativistic):
                findings.append(
                    Finding("QE.PSEUDO.SOC_INCOMPATIBLE", "error", f"{name} is not marked fully relativistic/spin-orbit capable")
                )
            elif has_so is not True and not fully_relativistic:
                findings.append(
                    Finding("QE.PSEUDO.SOC_UNKNOWN", "incomplete", f"Spin-orbit capability could not be verified for {name}")
                )
        evidence.append(
            {
                "label": item["label"],
                "filename": name,
                "sha256": actual_sha,
                "format": "upf" if upf_signature else "unrecognized",
                "declared_source": None if declaration is None else declaration.get("source"),
                "functional": functional,
                "pseudo_type": attributes.get("pseudo_type"),
                "relativistic": relativistic,
                "has_so": has_so,
            }
        )
    if len(functionals) > 1:
        findings.append(
            Finding("QE.PSEUDO.MIXED_FUNCTIONALS", "error", "Pseudopotential metadata reports multiple XC functionals")
        )
    selected = [item for item in findings if item.code.startswith("QE.PSEUDO.")]
    if any(item.severity == "error" for item in selected):
        status = "fail"
    elif any(item.severity == "incomplete" for item in selected):
        status = "incomplete"
    else:
        status = "pass"
    return status, evidence


def validate_runtime_paths(
    summary: dict[str, Any], run_dir: Path, pseudo_dir: Path | None, findings: list[Finding]
) -> str:
    if not run_dir.is_dir():
        findings.append(Finding("QE.RUNTIME.RUN_DIR", "error", "--run-dir is not an existing directory"))
        return "fail"
    prefix = summary.get("_prefix_value")
    if prefix is not None and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", prefix):
        findings.append(
            Finding("QE.RUNTIME.UNSAFE_PREFIX", "error", "prefix must be a safe path-neutral identifier")
        )

    def resolve_input_path(value: str | None) -> Path | None:
        if value is None or "$" in value or "~" in value:
            return None
        path = Path(value)
        return (path if path.is_absolute() else run_dir / path).resolve()

    input_pseudo = resolve_input_path(summary.get("_pseudo_dir_value"))
    if pseudo_dir is not None and input_pseudo != pseudo_dir.resolve():
        findings.append(
            Finding(
                "QE.RUNTIME.PSEUDO_DIR_MISMATCH",
                "error",
                "Input pseudo_dir does not resolve to --pseudo-dir from the declared --run-dir",
            )
        )
    input_outdir = resolve_input_path(summary.get("_outdir_value"))
    if input_outdir is None:
        findings.append(
            Finding("QE.RUNTIME.OUTDIR_UNRESOLVED", "error", "Input outdir could not be resolved without shell expansion")
        )
    elif not input_outdir.is_dir() or not os.access(input_outdir, os.W_OK | os.X_OK):
        findings.append(
            Finding("QE.RUNTIME.OUTDIR_UNAVAILABLE", "error", "Resolved outdir must already be a writable directory")
        )
    return gate_status(findings, ("QE.RUNTIME.",))


def validate_output(
    text: str,
    calculation: str,
    findings: list[Finding],
    expected_summary: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    version_matches = re.findall(r"Program\s+PWSCF\s+v\.?\s*([^\s]+)", text, flags=re.I)
    version_match = version_matches[0] if version_matches else None
    version = normalize_version(version_match) if version_match else None
    fatal = bool(re.search(r"Error in routine|%%%%+|SIG(?:SEGV|ABRT)|segmentation fault", text, flags=re.I))
    job_done_count = len(re.findall(r"JOB DONE\.", text))
    job_done = job_done_count == 1
    scf_not_converged = bool(re.search(r"convergence\s+NOT\s+achieved", text, flags=re.I))
    scf_converged = len(re.findall(r"convergence has been achieved", text, flags=re.I))
    if version is None:
        findings.append(Finding("QE.OUTPUT.VERSION_MISSING", "error", "Could not find the PWSCF version banner in output"))
    elif len(version_matches) != 1:
        findings.append(Finding("QE.OUTPUT.MULTIPLE_RUNS", "error", "Output contains multiple PWSCF version banners"))
    if fatal:
        findings.append(Finding("QE.OUTPUT.FATAL", "error", "Output contains a fatal QE/runtime marker"))
    if job_done_count == 0:
        findings.append(Finding("QE.OUTPUT.NO_JOB_DONE", "error", "Output does not contain JOB DONE."))
    elif job_done_count != 1:
        findings.append(Finding("QE.OUTPUT.MULTIPLE_JOB_DONE", "error", "Output contains multiple JOB DONE. markers"))
    if scf_not_converged:
        findings.append(Finding("QE.OUTPUT.SCF_NOT_CONVERGED", "error", "Output reports that electronic convergence was not achieved"))
    if calculation in {"scf", "relax", "vc-relax"} and scf_converged == 0:
        findings.append(Finding("QE.OUTPUT.NO_SCF_CONVERGENCE", "error", "No successful SCF convergence marker was found"))
    if calculation not in {"scf", "relax", "vc-relax"}:
        findings.append(
            Finding(
                "QE.OUTPUT.UNSUPPORTED_CALCULATION",
                "error",
                f"Automated completion audit is not implemented for pw.x calculation={calculation}",
            )
        )
    if calculation in {"relax", "vc-relax"} and not re.search(
        r"End of BFGS Geometry Optimization|bfgs converged", text, flags=re.I
    ):
        findings.append(Finding("QE.OUTPUT.IONIC_NOT_CONVERGED", "error", "No completed ionic-optimization marker was found"))
    echoed: dict[str, float | int | None] = {}
    echo_patterns: dict[str, tuple[str, Any]] = {
        "ibrav": (r"bravais-lattice index\s*=\s*(-?\d+)", int),
        "nat": (r"number of atoms/cell\s*=\s*(\d+)", int),
        "ntyp": (r"number of atomic types\s*=\s*(\d+)", int),
        "ecutwfc_ry": (r"kinetic-energy cutoff\s*=\s*([-+0-9.eEdD]+)\s*Ry", as_float),
        "ecutrho_ry": (r"charge density cutoff\s*=\s*([-+0-9.eEdD]+)\s*Ry", as_float),
    }
    for name, (pattern, converter) in echo_patterns.items():
        match = re.search(pattern, text, flags=re.I)
        echoed[name] = converter(match.group(1)) if match else None
    if expected_summary is not None:
        for name in echo_patterns:
            expected = expected_summary.get(name)
            actual = echoed[name]
            if expected is None:
                continue
            if actual is None:
                findings.append(
                    Finding("QE.OUTPUT.ECHO_MISSING", "error", f"Output does not echo required setting {name}")
                )
            elif isinstance(expected, float):
                if not math.isclose(float(actual), expected, rel_tol=1e-10, abs_tol=1e-12):
                    findings.append(
                        Finding("QE.OUTPUT.INPUT_MISMATCH", "error", f"Output {name} differs from audited input")
                    )
            elif actual != expected:
                findings.append(
                    Finding("QE.OUTPUT.INPUT_MISMATCH", "error", f"Output {name} differs from audited input")
                )
    total_energy_matches = re.findall(
        r"^\s*!\s+total energy\s*=\s*([-+0-9.eEdD]+)\s+Ry\b", text, flags=re.I | re.M
    )
    total_energy = as_float(total_energy_matches[-1]) if total_energy_matches else None
    status = gate_status(findings, ("QE.OUTPUT.",))
    summary = {
        "qe_version": version,
        "job_done": job_done,
        "successful_scf_cycles": scf_converged,
        "scf_iteration_lines": len(re.findall(r"iteration\s+#", text, flags=re.I)),
        "warning_lines": len(re.findall(r"^\s*Warning:", text, flags=re.I | re.M)),
        "echoed_settings": echoed,
        "observables": (
            {} if total_energy is None else {"total_energy": {"value": total_energy, "unit": "Ry"}}
        ),
    }
    return status, summary


def validate_stderr(text: str, findings: list[Finding]) -> tuple[str, dict[str, Any]]:
    """Audit separately captured runtime diagnostics without exposing their text."""
    nonempty_lines = [line for line in text.splitlines() if line.strip()]
    floating_point_exception_lines = sum(
        1
        for line in nonempty_lines
        if re.search(
            r"floating-point exceptions? are signalling|IEEE_(?:INVALID|DIVIDE_BY_ZERO|OVERFLOW|UNDERFLOW|DENORMAL)_FLAG",
            line,
            flags=re.I,
        )
    )
    fatal_lines = sum(
        1
        for line in nonempty_lines
        if re.search(r"Error in routine|%%%%+|SIG(?:SEGV|ABRT)|segmentation fault", line, flags=re.I)
    )
    warning_lines = sum(1 for line in nonempty_lines if re.search(r"\b(?:warning|warn)\b", line, flags=re.I))
    if floating_point_exception_lines:
        findings.append(
            Finding(
                "QE.STDERR.FLOATING_POINT_EXCEPTION",
                "error",
                "Separate stderr reports signalling IEEE floating-point exception flags",
            )
        )
    if fatal_lines:
        findings.append(
            Finding("QE.STDERR.FATAL", "error", "Separate stderr contains a fatal QE/runtime marker")
        )
    if nonempty_lines and not floating_point_exception_lines and not fatal_lines:
        findings.append(
            Finding(
                "QE.STDERR.NONEMPTY",
                "warning",
                "Separate stderr is nonempty and requires case-level review even though no deterministic fatal marker matched",
            )
        )
    return gate_status(findings, ("QE.STDERR.",)), {
        "nonempty_lines": len(nonempty_lines),
        "floating_point_exception_lines": floating_point_exception_lines,
        "fatal_lines": fatal_lines,
        "warning_lines": warning_lines,
    }


def convergence_parameter_evidence(summary: dict[str, Any]) -> dict[str, dict[str, float | str]]:
    """Return only scalar settings that the deterministic input parser actually verified."""

    candidates = {
        "ecutwfc": (summary.get("ecutwfc_ry"), "Ry"),
        "ecutrho": (summary.get("ecutrho_ry"), "Ry"),
        "conv_thr": (summary.get("conv_thr_ry"), "Ry"),
        "degauss": (summary.get("degauss_ry") if summary.get("occupations") == "smearing" else None, "Ry"),
        "k_point_count": ((summary.get("k_points") or {}).get("count"), "count"),
    }
    return {
        name: {"value": float(value), "unit": unit}
        for name, (value, unit) in candidates.items()
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))
    }


def mirror_pw_record() -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH, "official QE manifest")
    return next(item for item in manifest["input_manuals"] if item["name"] == "INPUT_PW")


def command_plan(args: argparse.Namespace) -> int:
    if not ID_RE.fullmatch(args.case_id) or not ID_RE.fullmatch(args.protocol_id):
        raise ValueError("case-id and protocol-id must be anonymized safe identifiers of 3-128 characters")
    if args.absolute_tolerance is None and args.relative_tolerance is None:
        raise ValueError("provide --absolute-tolerance or --relative-tolerance")
    if not args.objective.strip() or not args.observable.strip() or not args.observable_unit.strip():
        raise ValueError("objective, observable, and observable-unit must be nonempty")
    for value, label in [
        (args.absolute_tolerance, "absolute tolerance"),
        (args.relative_tolerance, "relative tolerance"),
    ]:
        if value is not None and (not math.isfinite(value) or value < 0):
            raise ValueError(f"{label} must be finite and nonnegative")
    normalized_qe_version = normalize_version(args.qe_version)
    if not re.fullmatch(r"\d+(?:\.\d+)+(?:[-+._A-Za-z0-9]*)?", normalized_qe_version):
        raise ValueError("qe-version must contain an explicit dotted numeric version")
    payload = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "case_id": args.case_id,
        "scientific_protocol_id": args.protocol_id,
        "task_type": args.task_type,
        "qe_version": normalized_qe_version,
        "objective": args.objective.strip(),
        "observable": {
            "name": args.observable.strip(),
            "unit": args.observable_unit.strip(),
            "absolute_tolerance": args.absolute_tolerance,
            "relative_tolerance": args.relative_tolerance,
        },
        "minimum_workflow": TASK_WORKFLOWS[args.task_type],
        "decision": "pass",
        "state": "plan_ready",
        "limitations": [
            "The minimum workflow is not a universal complete workflow.",
            "Material-, model-, and observable-specific controls may add stages and convergence dimensions.",
        ],
        "provenance": {"collector": "qe_guard", "collector_version": TOOL_VERSION, "generated_utc": generated_utc()},
    }
    write_json(payload, args.out)
    return 0


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def manual_record(executable: str) -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH, "official QE manifest")
    needle = executable.lower().removesuffix(".x")
    exact_name_matches = [
        item
        for item in manifest.get("input_manuals", [])
        if item["name"].lower().removeprefix("input_") == needle
    ]
    if len(exact_name_matches) == 1:
        return exact_name_matches[0]
    matches = []
    for item in manifest.get("input_manuals", []):
        program = str(item.get("program", "")).lower()
        if re.search(rf"\b{re.escape(needle)}\.x\b", program):
            matches.append(item)
    if len(matches) != 1:
        raise ValueError(f"Could not uniquely map executable {executable!r} to an official INPUT manual")
    return matches[0]


def live_fetch(url: str, timeout: float) -> bytes:
    """Fetch with verified TLS; use system curl only for a missing Python CA chain."""
    request = urllib.request.Request(url, headers={"User-Agent": "qe-guard/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.URLError as exc:
        if not isinstance(exc.reason, ssl.SSLCertVerificationError):
            raise
        curl = shutil.which("curl")
        if curl is None:
            raise
        completed = subprocess.run(
            [
                curl,
                "--fail",
                "--silent",
                "--show-error",
                "--location",
                "--max-time",
                str(timeout),
                url,
            ],
            check=True,
            capture_output=True,
            timeout=timeout + 5,
        )
        return completed.stdout


REFERENCE_PAYLOAD_HASH_BASIS = (
    "utf-8 bytes of the fenced text payload after removing the single wrapper separator newline"
)


def safe_local_reference_path(relative: str, label: str) -> Path:
    """Resolve one manifest/index path without permitting traversal or symlink substitution."""
    if not isinstance(relative, str) or not relative:
        raise ValueError(f"{label} path is missing")
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"{label} path escapes the references directory")
    try:
        root = REFERENCES.resolve(strict=True)
    except OSError as exc:
        raise ValueError("references directory is unavailable") from exc
    candidate = REFERENCES
    for part in relative_path.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError(f"{label} path uses a symlink")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise ValueError(f"{label} path is missing or escapes the references directory") from exc
    if not resolved.is_file():
        raise ValueError(f"{label} path is not a regular file")
    return resolved


def extract_local_reference_payload(text: str) -> str:
    """Extract the exact payload hashed by sync_official_manuals.py."""
    source_match = re.search(r"(?m)^- Official source SHA-256: `([0-9a-f]{64})`$", text)
    extracted_match = re.search(r"(?m)^- Extracted text SHA-256: `([0-9a-f]{64})`$", text)
    fence_match = re.search(r"(?m)^(`{3,})text$", text)
    if not source_match or not extracted_match or not fence_match:
        raise ValueError("local entry is missing provenance metadata or its text fence")
    fence = fence_match.group(1)
    payload_start = fence_match.end() + 1
    closing = re.search(rf"(?m)^{re.escape(fence)}$", text[payload_start:])
    if closing is None:
        raise ValueError("local entry is missing its closing text fence")
    closing_start = payload_start + closing.start()
    closing_end = payload_start + closing.end()
    fenced_text = text[payload_start:closing_start]
    if not fenced_text.endswith("\n"):
        raise ValueError("local entry payload is missing the wrapper separator newline")
    if text[closing_end:] != "\n":
        raise ValueError("local entry contains content outside its canonical closing fence")
    return fenced_text[:-1]


def render_expected_local_reference(record: dict[str, Any], section: dict[str, Any], payload: str) -> str:
    """Reconstruct the generated input-section wrapper to reject unmanifested local additions."""
    source_format = record.get("source_format")
    if source_format == "txt":
        content_status = "official TXT text split without substantive additions"
    elif source_format == "html":
        content_status = "official text extracted from official HTML without substantive additions"
    else:
        raise ValueError("input manual source_format is not txt or html")
    required_record_strings = ["name", "url", "retrieved_utc", "sha256"]
    if any(not isinstance(record.get(field), str) or not record[field] for field in required_record_strings):
        raise ValueError("input manual provenance metadata is incomplete")
    if not isinstance(section.get("title"), str) or not section["title"]:
        raise ValueError("input section title is missing")
    fence = "```"
    while fence in payload:
        fence += "`"
    lines = [
        f"# {record['name']} — {section['title']}",
        "",
        f"- Official source: {record['url']}",
        f"- Retrieved: {record['retrieved_utc']}",
        f"- Official source SHA-256: `{record['sha256']}`",
        f"- Extracted text SHA-256: `{section['sha256']}`",
    ]
    if record.get("last_modified"):
        lines.append(f"- Official Last-Modified: {record['last_modified']}")
    lines.extend(
        [
            f"- Content status: {content_status}; wrapper metadata added by the mirror script.",
            "",
            f"{fence}text",
            payload,
            fence,
            "",
        ]
    )
    return "\n".join(lines)


def verified_local_reference_entry(
    record: dict[str, Any],
    title: str,
    relative: str,
) -> tuple[str | None, dict[str, Any]]:
    """Bind an indexed entry to one manifest section and its exact generated local payload."""
    verification: dict[str, Any] = {
        "status": "fail",
        "hash_basis": REFERENCE_PAYLOAD_HASH_BASIS,
        "manifest_payload": {"sha256": None, "bytes": None},
        "observed_payload": {"sha256": None, "bytes": None},
        "canonical_wrapper_match": False,
    }
    try:
        sections = record.get("sections")
        if not isinstance(sections, list):
            raise ValueError("input manual sections metadata is missing")
        matches = [section for section in sections if isinstance(section, dict) and section.get("file") == relative]
        if len(matches) != 1:
            raise ValueError("indexed entry does not map to exactly one manifest section")
        section = matches[0]
        if section.get("title") != title:
            raise ValueError("indexed entry title differs from its manifest section")
        expected_sha256 = section.get("sha256")
        expected_bytes = section.get("bytes")
        if not isinstance(expected_sha256, str) or re.fullmatch(r"[a-f0-9]{64}", expected_sha256) is None:
            raise ValueError("manifest section payload SHA-256 is invalid")
        if not isinstance(expected_bytes, int) or isinstance(expected_bytes, bool) or expected_bytes < 0:
            raise ValueError("manifest section payload byte count is invalid")
        verification["manifest_payload"] = {"sha256": expected_sha256, "bytes": expected_bytes}
        path = safe_local_reference_path(relative, "input section")
        text = path.read_text(encoding="utf-8", errors="strict")
        payload = extract_local_reference_payload(text)
        payload_bytes = payload.encode("utf-8")
        observed_sha256 = hashlib.sha256(payload_bytes).hexdigest()
        observed_bytes = len(payload_bytes)
        verification["observed_payload"] = {"sha256": observed_sha256, "bytes": observed_bytes}
        if observed_sha256 != expected_sha256 or observed_bytes != expected_bytes:
            raise ValueError("local fenced payload differs from manifest SHA-256 or byte count")
        if text != render_expected_local_reference(record, section, payload):
            raise ValueError("local entry wrapper differs from its canonical generated form")
    except (OSError, UnicodeError, ValueError, KeyError) as exc:
        verification["reason"] = str(exc)
        return None, verification
    verification["status"] = "verified"
    verification["canonical_wrapper_match"] = True
    verification["reason"] = None
    return text, verification


def reference_entry_page(
    text: str,
    relative: str,
    max_chars: int,
    continuation_token: str | None,
    full_entry: bool,
) -> dict[str, Any]:
    """Return one content-addressed page without implying that a partial page is the full entry."""
    if max_chars <= 0:
        raise ValueError("--max-chars must be a positive integer")
    if full_entry and continuation_token is not None:
        raise ValueError("--full-entry cannot be combined with --continuation-token")

    content_bytes = text.encode("utf-8")
    content_sha256 = hashlib.sha256(content_bytes).hexdigest()
    entry_identity = hashlib.sha256(f"references/{relative}\0{content_sha256}".encode("utf-8")).hexdigest()
    start_character = 0
    if continuation_token is not None:
        match = re.fullmatch(r"qe-reference-v1:([a-f0-9]{64}):([1-9][0-9]*)", continuation_token)
        if match is None:
            raise ValueError("invalid --continuation-token format")
        token_identity, token_offset = match.groups()
        start_character = int(token_offset)
        if token_identity != entry_identity or start_character >= len(text):
            raise ValueError("--continuation-token does not identify a remaining page of this reference entry")

    end_character = len(text) if full_entry else min(len(text), start_character + max_chars)
    excerpt = text[start_character:end_character]
    byte_start = len(text[:start_character].encode("utf-8"))
    byte_end = byte_start + len(excerpt.encode("utf-8"))
    truncated = end_character < len(text)
    next_token = f"qe-reference-v1:{entry_identity}:{end_character}" if truncated else None
    complete_entry_returned = start_character == 0 and end_character == len(text)
    return {
        "excerpt": excerpt,
        "total_bytes": len(content_bytes),
        "returned_range": {
            "unit": "utf-8-bytes",
            "start": byte_start,
            "end_exclusive": byte_end,
        },
        "content_sha256": content_sha256,
        "truncated": truncated,
        "continuation_token": next_token,
        "complete_entry_returned": complete_entry_returned,
    }


def command_reference(args: argparse.Namespace) -> int:
    record = manual_record(args.executable)
    version_match = normalize_version(args.qe_version) == normalize_version(str(record.get("version", "")))
    index_path = safe_local_reference_path(record["index_file"], "input manual index")
    links = re.findall(r"^- \[([^]]+)\]\(([^)]+)\)$", index_path.read_text(encoding="utf-8"), flags=re.M)
    query = normalize_text(args.term)
    matches = [(title, file) for title, file in links if query in normalize_text(title)]
    if (args.continuation_token is not None or args.full_entry) and len(matches) != 1:
        raise ValueError("--continuation-token and --full-entry require exactly one reference match")
    result_matches: list[dict[str, Any]] = []
    for title, relative in matches:
        text, entry_verification = verified_local_reference_entry(record, title, relative)
        result_match = {
            "title": title,
            "reference_file": f"references/{relative}",
            "official_url": record["url"],
            "manual_version": record.get("version"),
            "retrieved_utc": record.get("retrieved_utc"),
            "entry_verification": entry_verification,
        }
        if text is not None:
            result_match.update(
                reference_entry_page(
                    text,
                    relative,
                    args.max_chars,
                    args.continuation_token,
                    args.full_entry,
                )
            )
        result_matches.append(result_match)

    live_status = "offline_cache" if args.offline else "not_checked"
    live_sha = None
    if args.live_check:
        try:
            content = live_fetch(record["url"], args.timeout)
            live_sha = hashlib.sha256(content).hexdigest()
            live_status = "match" if live_sha == record["sha256"] else "mirror_stale"
        except Exception as exc:  # network/SSL errors are intentionally fail-closed
            live_status = "unavailable"
            network_error = type(exc).__name__
        else:
            network_error = None
    else:
        network_error = None

    if not version_match:
        decision = "blocked_version_mismatch"
    elif not matches:
        decision = "blocked_not_found"
    elif len(matches) != 1:
        decision = "blocked_ambiguous"
    elif result_matches[0]["entry_verification"]["status"] != "verified":
        decision = "blocked_local_entry_integrity"
    elif not (args.live_check or args.offline):
        decision = "blocked_retrieval_mode_unspecified"
    elif live_status in {"mirror_stale", "unavailable"}:
        decision = "blocked_live_check"
    elif not result_matches[0]["complete_entry_returned"]:
        decision = "blocked_partial_entry"
    elif live_status == "offline_cache":
        decision = "cached_only"
    else:
        decision = "pass"

    payload = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "query": {"executable": args.executable, "term": args.term, "qe_version": normalize_version(args.qe_version)},
        "manual": {
            "name": record["name"],
            "version": record.get("version"),
            "official_url": record["url"],
            "retrieved_utc": record.get("retrieved_utc"),
            "cached_sha256": record["sha256"],
        },
        "version_match": version_match,
        "live_check": {"status": live_status, "sha256": live_sha, "error_type": network_error},
        "matches": result_matches,
        "decision": decision,
        "required_disclosure": (
            f"Exact behavior for QE {normalize_version(args.qe_version)} is not verified by a matching official input manual in this mirror."
            if not version_match
            else (
                "The matched local entry did not satisfy its manifest payload and canonical-wrapper integrity contract."
                if len(result_matches) == 1
                and result_matches[0]["entry_verification"]["status"] != "verified"
                else (
                    "Only a partial page of the matched official entry was returned; the complete entry is not verified by this response."
                    if len(result_matches) == 1 and not result_matches[0]["complete_entry_returned"]
                    else None
                )
            )
        ),
        "provenance": {"collector": "qe_guard", "collector_version": TOOL_VERSION, "generated_utc": generated_utc()},
    }
    write_json(payload, args.out)
    if decision == "pass":
        return 0
    if decision == "cached_only":
        return 3
    return 2


def command_audit(args: argparse.Namespace) -> int:
    input_path = args.input.resolve()
    if not input_path.is_file():
        raise ValueError("--input must identify a readable file")
    input_text = input_path.read_text(encoding="utf-8", errors="strict")
    summary, findings = validate_pw_input(input_text)
    if args.stderr and not args.output:
        raise ValueError("--stderr is only valid together with --output")
    if args.out:
        report_path = args.out.resolve()
        protected_paths = {
            path.resolve()
            for path in [args.input, args.output, args.stderr, args.plan, args.parent_manifest, args.pseudo_manifest]
            if path is not None
        }
        if args.pseudo_dir:
            protected_paths.update((args.pseudo_dir.resolve() / item["pseudopotential"]).resolve() for item in summary["species"])
        if report_path in protected_paths:
            raise ValueError("--out must not overwrite an input, output, plan, manifest, or pseudopotential artifact")

    manual = mirror_pw_record()
    expected_version = normalize_version(args.expected_version)
    manual_version = normalize_version(str(manual.get("version", "")))
    if expected_version != manual_version:
        findings.append(
            Finding(
                "QE.VERSION.MANUAL_MISMATCH",
                "error",
                f"Exact behavior for QE {expected_version} is not verified by a matching official input manual in this mirror.",
                manual["url"],
            )
        )
    version_status = gate_status(findings, ("QE.VERSION.",))

    if args.plan:
        try:
            plan = load_json(args.plan, "QE plan")
        except ValueError as exc:
            plan = None
            findings.append(Finding("QE.PLAN.INVALID_JSON", "error", str(exc)))
            plan_status = "fail"
        else:
            plan_status = validate_plan(plan, summary["calculation"], expected_version, findings)
    else:
        plan = None
        findings.append(Finding("QE.PLAN.NOT_ASSESSED", "incomplete", "Provide --plan; no scientific objective/tolerance contract was assessed"))
        plan_status = "incomplete"

    parent = load_json(args.parent_manifest, "parent run manifest") if args.parent_manifest else None
    ancestry_status = validate_parent_manifest(
        parent,
        summary["calculation"],
        summary["restart_mode"],
        expected_version,
        plan,
        summary.get("_prefix_value"),
        findings,
    )
    runtime_status = validate_runtime_paths(summary, args.run_dir.resolve(), args.pseudo_dir, findings)
    pseudo_status, pseudo_evidence = validate_pseudopotentials(
        summary["species"], args.pseudo_dir, args.pseudo_manifest, summary["spin_orbit"], findings
    )
    input_status = gate_status(findings, ("QE.INPUT.", "QE.PW.", "QE.POLICY."))

    output_summary = None
    output_status = "not_requested"
    output_sha = None
    stderr_summary = None
    stderr_status = "not_requested"
    stderr_sha = None
    if args.output:
        output_path = args.output.resolve()
        if not output_path.is_file():
            findings.append(Finding("QE.OUTPUT.FILE", "error", "--output is not a readable file"))
            output_status = "fail"
        else:
            output_text = output_path.read_text(encoding="utf-8", errors="replace")
            output_sha = sha256_file(output_path)
            output_status, output_summary = validate_output(
                output_text, summary["calculation"], findings, expected_summary=summary
            )
            output_version = output_summary.get("qe_version") if output_summary else None
            if output_version and normalize_version(output_version) != expected_version:
                findings.append(Finding("QE.VERSION.OUTPUT_MISMATCH", "error", "Output QE version differs from --expected-version"))
                version_status = "fail"
        if args.stderr is None:
            findings.append(
                Finding(
                    "QE.STDERR.NOT_PROVIDED",
                    "error",
                    "A completion audit requires the separately captured stderr artifact",
                )
            )
            stderr_status = "fail"
        else:
            stderr_path = args.stderr.resolve()
            if not stderr_path.is_file():
                findings.append(Finding("QE.STDERR.FILE", "error", "--stderr is not a readable file"))
                stderr_status = "fail"
            else:
                stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
                stderr_sha = sha256_file(stderr_path)
                stderr_status, stderr_summary = validate_stderr(stderr_text, findings)

    gates = {
        "plan": plan_status,
        "input_integrity": input_status,
        "pseudopotential_provenance": pseudo_status,
        "official_version_match": version_status,
        "parent_ancestry": ancestry_status,
        "runtime_paths": runtime_status,
        "execution_completion": output_status,
        "runtime_diagnostics": stderr_status,
        "observable_convergence": "not_assessed",
        "physical_validity": "not_assessed",
    }
    requested = [plan_status, input_status, pseudo_status, version_status, ancestry_status, runtime_status]
    if args.output:
        requested.extend([output_status, stderr_status])
    scope_decision = "pass" if all(status == "pass" for status in requested) else "blocked"
    public_summary = {key: value for key, value in summary.items() if not key.startswith("_")}
    payload = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "scope": "pw.x input" + (", stdout, and stderr" if args.output else ""),
        "decision": scope_decision,
        "scientific_claim_decision": "blocked",
        "gates": gates,
        "summary": public_summary,
        "output_summary": output_summary,
        "stderr_summary": stderr_summary,
        "evidence": {
            "input": {"role": "pw_input", "sha256": sha256_file(input_path)},
            "output": None if not args.output else {"role": "pw_output", "sha256": output_sha},
            "stderr": None if not args.output else {"role": "runtime_stderr", "sha256": stderr_sha},
            "plan": None if not args.plan else {"role": "qe_plan", "sha256": sha256_file(args.plan)},
            "convergence_parameters": convergence_parameter_evidence(public_summary),
            "observables": {} if output_summary is None else output_summary.get("observables", {}),
            "pseudopotentials": pseudo_evidence,
            "pseudopotential_manifest": (
                None
                if not args.pseudo_manifest or not args.pseudo_manifest.is_file()
                else {"role": "pseudopotential_manifest", "sha256": sha256_file(args.pseudo_manifest)}
            ),
            "plan_record_id": None if plan is None else plan.get("scientific_protocol_id"),
            "parent_record_id": None if parent is None else parent.get("record_id"),
            "parent_manifest": (
                None
                if not args.parent_manifest or not args.parent_manifest.is_file()
                else {"role": "parent_run_manifest", "sha256": sha256_file(args.parent_manifest)}
            ),
        },
        "findings": [item.as_dict() for item in findings],
        "required_remaining_gates": [
            "observable-specific convergence under a fixed protocol",
            "claim-specific physical/model validation",
        ],
        "provenance": {"collector": "qe_guard", "collector_version": TOOL_VERSION, "generated_utc": generated_utc()},
    }
    write_json(payload, args.out)
    return 0 if scope_decision == "pass" else 2


def command_convergence(args: argparse.Namespace) -> int:
    if args.tail < 3:
        raise ValueError("--tail must be at least 3")
    if not ID_RE.fullmatch(args.protocol_id):
        raise ValueError("--protocol-id must be an anonymized safe identifier of 3-128 characters")
    if not all(value.strip() for value in [args.parameter, args.parameter_unit, args.observable, args.observable_unit]):
        raise ValueError("parameter, observable, and units must be nonempty")
    findings: list[Finding] = []
    plan = load_json(args.plan, "QE plan")
    plan_sha = sha256_file(args.plan)
    provenance = plan.get("provenance")
    if (
        plan.get("schema_version") != REPORT_SCHEMA_VERSION
        or plan.get("decision") != "pass"
        or not isinstance(provenance, dict)
        or provenance.get("collector") != "qe_guard"
        or provenance.get("collector_version") != TOOL_VERSION
    ):
        findings.append(Finding("QE.CONVERGENCE.PLAN_PROVENANCE", "error", "Convergence plan was not produced by the current qe_guard"))
    if plan.get("scientific_protocol_id") != args.protocol_id:
        findings.append(Finding("QE.CONVERGENCE.PLAN_PROTOCOL", "error", "Convergence plan protocol differs from --protocol-id"))
    planned_observable = plan.get("observable")
    if not isinstance(planned_observable, dict):
        findings.append(Finding("QE.CONVERGENCE.PLAN_OBSERVABLE", "error", "Convergence plan has no observable contract"))
    else:
        if planned_observable.get("name") != args.observable or planned_observable.get("unit") != args.observable_unit:
            findings.append(Finding("QE.CONVERGENCE.PLAN_OBSERVABLE", "error", "Requested observable/unit differs from the plan"))
        for argument_value, field, label in [
            (args.absolute_tolerance, "absolute_tolerance", "absolute"),
            (args.relative_tolerance, "relative_tolerance", "relative"),
        ]:
            planned_value = planned_observable.get(field)
            same = argument_value is None and planned_value is None
            if argument_value is not None and isinstance(planned_value, (int, float)) and not isinstance(planned_value, bool):
                same = math.isclose(argument_value, float(planned_value), rel_tol=1e-12, abs_tol=0.0)
            if not same:
                findings.append(
                    Finding("QE.CONVERGENCE.PLAN_TOLERANCE", "error", f"Requested {label} tolerance differs from the plan")
                )

    rows: list[dict[str, str]] = []
    with args.csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = [
            "setting",
            "observable",
            "protocol_id",
            "audit_report",
            "input_file",
            "output_file",
            "stderr_file",
        ]
        if reader.fieldnames != required:
            raise ValueError(
                "CSV requires exactly setting, observable, protocol_id, audit_report, input_file, output_file, and stderr_file columns"
            )
        rows = list(reader)
    if args.out:
        report_path = args.out.resolve()
        protected_paths = {args.csv.resolve(), args.plan.resolve()}
        csv_root = args.csv.resolve().parent
        for row in rows:
            for field in ["audit_report", "input_file", "output_file", "stderr_file"]:
                raw = row.get(field)
                if not isinstance(raw, str) or not raw.strip():
                    continue
                candidate = Path(raw)
                protected_paths.add((candidate if candidate.is_absolute() else csv_root / candidate).resolve())
        if report_path in protected_paths:
            raise ValueError("--out must not overwrite the CSV, plan, audit report, input, or output evidence")
    points: list[dict[str, Any]] = []
    audit_hashes: list[str] = []
    input_hashes: list[str] = []
    output_hashes: list[str] = []
    csv_root = args.csv.resolve().parent

    def evidence_path(raw: str | None, row_number: int, role: str) -> Path | None:
        if not isinstance(raw, str) or not raw.strip():
            findings.append(Finding(f"QE.CONVERGENCE.{role.upper()}_MISSING", "error", f"Row {row_number} has no {role} path"))
            return None
        candidate = Path(raw)
        candidate = (candidate if candidate.is_absolute() else csv_root / candidate).resolve()
        if not candidate.is_file():
            findings.append(
                Finding(f"QE.CONVERGENCE.{role.upper()}_UNREADABLE", "error", f"Row {row_number} {role} is not a readable file")
            )
            return None
        return candidate

    for number, row in enumerate(rows, start=2):
        if None in row:
            findings.append(Finding("QE.CONVERGENCE.ROW_WIDTH", "error", f"Row {number} has too many CSV fields"))
            continue
        if row["protocol_id"] != args.protocol_id:
            findings.append(Finding("QE.CONVERGENCE.PROTOCOL_MISMATCH", "error", f"Row {number} has a different protocol_id"))
        setting = as_float(row["setting"])
        observable = as_float(row["observable"])
        if setting is None or observable is None or not math.isfinite(setting) or not math.isfinite(observable):
            findings.append(Finding("QE.CONVERGENCE.NONFINITE", "error", f"Row {number} contains invalid/nonfinite data"))
            continue

        audit_path = evidence_path(row["audit_report"], number, "audit_report")
        input_path = evidence_path(row["input_file"], number, "input_file")
        output_path = evidence_path(row["output_file"], number, "output_file")
        stderr_path = evidence_path(row["stderr_file"], number, "stderr_file")
        if audit_path is None or input_path is None or output_path is None or stderr_path is None:
            continue
        try:
            audit = load_json(audit_path, f"row {number} QE audit report")
        except ValueError as exc:
            findings.append(Finding("QE.CONVERGENCE.AUDIT_INVALID", "error", str(exc)))
            continue

        audit_sha = sha256_file(audit_path)
        input_sha = sha256_file(input_path)
        output_sha = sha256_file(output_path)
        stderr_sha = sha256_file(stderr_path)
        audit_hashes.append(audit_sha)
        input_hashes.append(input_sha)
        output_hashes.append(output_sha)

        provenance = audit.get("provenance")
        if not isinstance(provenance, dict) or provenance.get("collector") != "qe_guard" or provenance.get("collector_version") != TOOL_VERSION:
            findings.append(
                Finding("QE.CONVERGENCE.AUDIT_PROVENANCE", "error", f"Row {number} was not produced by qe_guard {TOOL_VERSION}")
            )
        if audit.get("schema_version") != REPORT_SCHEMA_VERSION or audit.get("scope") != "pw.x input, stdout, and stderr":
            findings.append(Finding("QE.CONVERGENCE.AUDIT_SCOPE", "error", f"Row {number} is not a current pw.x input/stdout/stderr audit"))
        if audit.get("decision") != "pass":
            findings.append(Finding("QE.CONVERGENCE.AUDIT_BLOCKED", "error", f"Row {number} audit decision is not pass"))
        gates = audit.get("gates")
        if not isinstance(gates, dict) or any(gates.get(name) != "pass" for name in CONVERGENCE_AUDIT_GATES):
            findings.append(Finding("QE.CONVERGENCE.AUDIT_GATE", "error", f"Row {number} audit has an incomplete or failed required gate"))
        evidence = audit.get("evidence")
        if not isinstance(evidence, dict):
            findings.append(Finding("QE.CONVERGENCE.AUDIT_EVIDENCE", "error", f"Row {number} audit evidence is missing"))
            continue
        if evidence.get("plan_record_id") != args.protocol_id:
            findings.append(Finding("QE.CONVERGENCE.AUDIT_PROTOCOL", "error", f"Row {number} audit is bound to a different protocol"))
        recorded_plan = evidence.get("plan")
        if (
            not isinstance(recorded_plan, dict)
            or not SHA256_RE.fullmatch(str(recorded_plan.get("sha256", "")))
            or recorded_plan.get("sha256") != plan_sha
        ):
            findings.append(Finding("QE.CONVERGENCE.PLAN_HASH", "error", f"Row {number} audit does not match the supplied plan"))

        recorded_input = evidence.get("input")
        recorded_output = evidence.get("output")
        recorded_stderr = evidence.get("stderr")
        if (
            not isinstance(recorded_input, dict)
            or not SHA256_RE.fullmatch(str(recorded_input.get("sha256", "")))
            or recorded_input.get("sha256") != input_sha
        ):
            findings.append(Finding("QE.CONVERGENCE.INPUT_HASH", "error", f"Row {number} input does not match its audit"))
        if (
            not isinstance(recorded_output, dict)
            or not SHA256_RE.fullmatch(str(recorded_output.get("sha256", "")))
            or recorded_output.get("sha256") != output_sha
        ):
            findings.append(Finding("QE.CONVERGENCE.OUTPUT_HASH", "error", f"Row {number} output does not match its audit"))
        if (
            not isinstance(recorded_stderr, dict)
            or not SHA256_RE.fullmatch(str(recorded_stderr.get("sha256", "")))
            or recorded_stderr.get("sha256") != stderr_sha
        ):
            findings.append(Finding("QE.CONVERGENCE.STDERR_HASH", "error", f"Row {number} stderr does not match its audit"))

        parameters = evidence.get("convergence_parameters")
        parameter_evidence = parameters.get(args.parameter) if isinstance(parameters, dict) else None
        if not isinstance(parameter_evidence, dict):
            findings.append(
                Finding("QE.CONVERGENCE.PARAMETER_UNSUPPORTED", "error", f"Row {number} audit has no verified {args.parameter} evidence")
            )
        else:
            verified_setting = as_float(str(parameter_evidence.get("value", "")))
            if parameter_evidence.get("unit") != args.parameter_unit:
                findings.append(Finding("QE.CONVERGENCE.PARAMETER_UNIT", "error", f"Row {number} parameter unit differs from the audit"))
            if verified_setting is None or not math.isclose(verified_setting, setting, rel_tol=1e-12, abs_tol=0.0):
                findings.append(Finding("QE.CONVERGENCE.SETTING_MISMATCH", "error", f"Row {number} setting differs from the audited input"))

        observables = evidence.get("observables")
        observable_evidence = observables.get(args.observable) if isinstance(observables, dict) else None
        if not isinstance(observable_evidence, dict):
            findings.append(
                Finding("QE.CONVERGENCE.OBSERVABLE_UNSUPPORTED", "error", f"Row {number} audit has no verified {args.observable} evidence")
            )
        else:
            verified_observable = as_float(str(observable_evidence.get("value", "")))
            if observable_evidence.get("unit") != args.observable_unit:
                findings.append(Finding("QE.CONVERGENCE.OBSERVABLE_UNIT", "error", f"Row {number} observable unit differs from the audit"))
            if verified_observable is None or not math.isclose(
                verified_observable, observable, rel_tol=1e-12, abs_tol=1e-14
            ):
                findings.append(Finding("QE.CONVERGENCE.OBSERVABLE_MISMATCH", "error", f"Row {number} observable differs from the audited output"))

        points.append(
            {
                "setting": setting,
                "observable": observable,
                "audit_sha256": audit_sha,
                "input_sha256": input_sha,
                "output_sha256": output_sha,
                "stderr_sha256": stderr_sha,
            }
        )
    if len({point["setting"] for point in points}) != len(points):
        findings.append(Finding("QE.CONVERGENCE.DUPLICATE_SETTING", "error", "Convergence settings must be unique"))
    for hashes, code, message in [
        (audit_hashes, "QE.CONVERGENCE.DUPLICATE_AUDIT", "Each setting requires a distinct audit report"),
        (input_hashes, "QE.CONVERGENCE.DUPLICATE_INPUT", "Each setting requires a distinct audited input"),
        (output_hashes, "QE.CONVERGENCE.DUPLICATE_OUTPUT", "Each setting requires a distinct audited output"),
    ]:
        if len(set(hashes)) != len(hashes):
            findings.append(Finding(code, "error", message))
    if len(points) < args.tail:
        findings.append(Finding("QE.CONVERGENCE.TOO_FEW_POINTS", "error", f"Need at least tail={args.tail} valid points"))
    if args.absolute_tolerance is None and args.relative_tolerance is None:
        findings.append(Finding("QE.CONVERGENCE.NO_TOLERANCE", "error", "Provide an absolute or relative tolerance"))
    for value, label in [(args.absolute_tolerance, "absolute"), (args.relative_tolerance, "relative")]:
        if value is not None and (not math.isfinite(value) or value < 0):
            findings.append(Finding("QE.CONVERGENCE.INVALID_TOLERANCE", "error", f"{label} tolerance must be finite and nonnegative"))

    points.sort(key=lambda point: point["setting"], reverse=args.direction == "decreasing")
    deltas: list[dict[str, float]] = []
    stable = False
    if not any(item.severity == "error" for item in findings):
        tail = points[-args.tail :]
        stable = True
        for left_point, right_point in zip(tail, tail[1:]):
            left = left_point["observable"]
            right = right_point["observable"]
            delta = abs(right - left)
            allowed = (args.absolute_tolerance or 0.0) + (args.relative_tolerance or 0.0) * max(abs(left), abs(right))
            deltas.append({"delta": delta, "allowed": allowed})
            stable = stable and delta <= allowed
        if not stable:
            findings.append(Finding("QE.CONVERGENCE.UNSTABLE_TAIL", "error", "The strict-end tail exceeds the declared tolerance"))

    status = "pass" if stable and not any(item.severity == "error" for item in findings) else "fail"
    payload = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "decision": status,
        "scientific_claim_decision": "blocked",
        "scientific_claim_blockers": ["physical_validity", "unassessed_convergence_dimensions"],
        "protocol_id": args.protocol_id,
        "parameter": {"name": args.parameter, "unit": args.parameter_unit, "strict_direction": args.direction},
        "observable": {"name": args.observable, "unit": args.observable_unit},
        "tolerance": {"absolute": args.absolute_tolerance, "relative": args.relative_tolerance},
        "tail_size": args.tail,
        "points": points,
        "tail_deltas": deltas,
        "findings": [item.as_dict() for item in findings],
        "limitations": [
            "A stable tail is evidence only for this observable, protocol, sampled settings, and tolerance.",
            "This check does not prove monotonicity, absence of false plateaus, or physical/model validity.",
        ],
        "evidence": {"role": "convergence_table", "sha256": sha256_file(args.csv)},
        "provenance": {"collector": "qe_guard", "collector_version": TOOL_VERSION, "generated_utc": generated_utc()},
    }
    write_json(payload, args.out)
    return 0 if status == "pass" else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan", help="Create a minimum scientific objective/tolerance contract")
    plan.add_argument("--case-id", required=True)
    plan.add_argument("--protocol-id", required=True)
    plan.add_argument("--task-type", choices=sorted(TASK_WORKFLOWS), required=True)
    plan.add_argument("--qe-version", required=True)
    plan.add_argument("--objective", required=True)
    plan.add_argument("--observable", required=True)
    plan.add_argument("--observable-unit", required=True)
    plan.add_argument("--absolute-tolerance", type=float)
    plan.add_argument("--relative-tolerance", type=float)
    plan.add_argument("--out", type=Path, required=True)
    plan.set_defaults(handler=command_plan)

    reference = subparsers.add_parser("reference", help="Resolve one official input-manual entry")
    reference.add_argument("--executable", required=True)
    reference.add_argument("--term", required=True)
    reference.add_argument("--qe-version", required=True)
    mode = reference.add_mutually_exclusive_group()
    mode.add_argument("--live-check", action="store_true")
    mode.add_argument("--offline", action="store_true")
    reference.add_argument("--timeout", type=float, default=20.0)
    reference.add_argument("--max-chars", type=int, default=6000)
    reference.add_argument("--continuation-token")
    reference.add_argument("--full-entry", action="store_true")
    reference.add_argument("--out", type=Path)
    reference.set_defaults(handler=command_reference)

    audit = subparsers.add_parser("audit", help="Fail-closed pw.x input/output audit")
    audit.add_argument("--input", type=Path, required=True)
    audit.add_argument("--output", type=Path)
    audit.add_argument("--stderr", type=Path, help="Separately captured stderr; required with --output.")
    audit.add_argument("--run-dir", type=Path, required=True)
    audit.add_argument("--pseudo-dir", type=Path)
    audit.add_argument("--pseudo-manifest", type=Path)
    audit.add_argument("--expected-version", required=True)
    audit.add_argument("--plan", type=Path)
    audit.add_argument("--parent-manifest", type=Path)
    audit.add_argument("--out", type=Path)
    audit.set_defaults(handler=command_audit)

    convergence = subparsers.add_parser("convergence", help="Check a fixed-protocol stable tail")
    convergence.add_argument("--csv", type=Path, required=True)
    convergence.add_argument("--plan", type=Path, required=True)
    convergence.add_argument("--protocol-id", required=True)
    convergence.add_argument("--parameter", required=True)
    convergence.add_argument("--parameter-unit", required=True)
    convergence.add_argument("--observable", required=True)
    convergence.add_argument("--observable-unit", required=True)
    convergence.add_argument("--direction", choices=["increasing", "decreasing"], required=True)
    convergence.add_argument("--absolute-tolerance", type=float)
    convergence.add_argument("--relative-tolerance", type=float)
    convergence.add_argument("--tail", type=int, default=3)
    convergence.add_argument("--out", type=Path)
    convergence.set_defaults(handler=command_convergence)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.handler(args)
    except (OSError, UnicodeError, ValueError, KeyError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
