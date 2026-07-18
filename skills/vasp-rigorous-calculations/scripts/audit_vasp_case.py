#!/usr/bin/env python3
"""Fail-closed VASP input/run audit without exposing private paths or POTCAR contents."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


AUDIT_SCHEMA_VERSION = "2.0"
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
MIRROR_MANIFEST = SKILL_ROOT / "references" / "official-wiki" / "manifest.json"

TRUE_VALUES = {"T", ".TRUE.", "TRUE", "1", "YES", "Y"}
FALSE_VALUES = {"F", ".FALSE.", "FALSE", "0", "NO", "N"}
FLOAT_PATTERN = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?")
INTEGER_PATTERN = re.compile(r"[-+]?\d+")
RUN_TASKS = {
    "generic",
    "static",
    "relax",
    "bands",
    "dos",
    "phonon",
    "neb",
    "md",
    "optics",
    "response",
    "hybrid",
    "gw",
    "defect",
    "surface",
}
STATIC_TASKS = {"static", "bands", "dos", "optics", "response", "hybrid", "gw"}
BOOLEAN_TAGS = {
    "LCHARG",
    "LCALCEPS",
    "LDAU",
    "LDIPOL",
    "LELF",
    "LEPSILON",
    "LHFCALC",
    "LNONCOLLINEAR",
    "LOPTICS",
    "LSORBIT",
    "LWAVE",
}
FLOAT_TAGS = {"AEXX", "EDIFF", "EDIFFG", "ENCUT", "HFSCREEN", "KSPACING", "NELECT", "SIGMA"}
INTEGER_TAGS = {"IBRION", "ICHARG", "ISIF", "ISMEAR", "ISPIN", "ISTART", "LDAUTYPE", "NBANDS", "NELM", "NSW"}
SAFE_VALUE_TAGS = BOOLEAN_TAGS | FLOAT_TAGS | INTEGER_TAGS | {
    "GGA",
    "IVDW",
    "KGAMMA",
    "LDAUJ",
    "LDAUL",
    "LDAUU",
    "MAGMOM",
    "METAGGA",
    "PREC",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite_float(token: str, context: str) -> float:
    if not FLOAT_PATTERN.fullmatch(token.strip()):
        raise ValueError(f"{context} is not one finite numeric scalar")
    value = float(token)
    if not math.isfinite(value):
        raise ValueError(f"{context} is not finite")
    return value


def strict_integer(token: str, context: str) -> int:
    if not INTEGER_PATTERN.fullmatch(token.strip()):
        raise ValueError(f"{context} is not one integer")
    return int(token)


def strip_comment(text: str) -> str:
    positions = [pos for marker in ("!", "#") if (pos := text.find(marker)) >= 0]
    return text[: min(positions)] if positions else text


def parse_incar(path: Path) -> tuple[dict[str, str], list[str], list[dict[str, Any]]]:
    tags: dict[str, str] = {}
    duplicates: list[str] = []
    malformed: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(errors="replace").splitlines(), 1):
        cleaned = strip_comment(raw).strip()
        if not cleaned:
            continue
        for statement in cleaned.split(";"):
            statement = statement.strip()
            if not statement:
                continue
            if "=" not in statement:
                malformed.append({"line": line_number, "reason": "missing-equals"})
                continue
            key, value = statement.split("=", 1)
            key = key.strip().upper()
            value = value.strip()
            if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
                malformed.append({"line": line_number, "reason": "invalid-tag-name"})
                continue
            if not value:
                malformed.append({"line": line_number, "reason": "empty-value", "tag": key})
                continue
            if key in tags:
                duplicates.append(key)
            tags[key] = value
    return tags, sorted(set(duplicates)), malformed


def logical_value(value: str, tag: str) -> bool:
    token = value.strip().upper()
    if token in TRUE_VALUES:
        return True
    if token in FALSE_VALUES:
        return False
    raise ValueError(f"{tag} is not an explicit VASP logical value")


def numeric_vector(value: str, tag: str, integer: bool = False) -> list[float | int]:
    result: list[float | int] = []
    for token in value.replace(",", " ").split():
        repeat = 1
        scalar = token
        if "*" in token:
            repeat_text, scalar = token.split("*", 1)
            repeat = strict_integer(repeat_text, f"{tag} repetition")
            if repeat <= 0:
                raise ValueError(f"{tag} repetition must be positive")
        parsed: float | int
        parsed = strict_integer(scalar, tag) if integer else finite_float(scalar, tag)
        result.extend([parsed] * repeat)
    if not result:
        raise ValueError(f"{tag} has no values")
    return result


def determinant_3x3(matrix: list[list[float]]) -> float:
    a, b, c = matrix
    return (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )


def parse_poscar(path: Path) -> dict[str, Any]:
    lines = [line.strip() for line in path.read_text(errors="replace").splitlines()]
    if len(lines) < 8:
        raise ValueError("POSCAR has fewer than 8 lines")
    scale_tokens = lines[1].split()
    if len(scale_tokens) not in {1, 3}:
        raise ValueError("POSCAR scale line must contain one or three numbers")
    scale = [finite_float(token, "POSCAR scale") for token in scale_tokens]
    if len(scale) == 1 and scale[0] == 0:
        raise ValueError("POSCAR scalar scale must be nonzero")
    if len(scale) == 3 and any(value <= 0 for value in scale):
        raise ValueError("POSCAR three-component scale values must be positive")

    lattice: list[list[float]] = []
    for index in range(2, 5):
        tokens = lines[index].split()
        if len(tokens) != 3:
            raise ValueError(f"POSCAR lattice vector line {index + 1} must contain three numbers")
        lattice.append([finite_float(token, f"POSCAR lattice vector line {index + 1}") for token in tokens])
    raw_determinant = determinant_3x3(lattice)
    if abs(raw_determinant) < 1e-14:
        raise ValueError("POSCAR lattice vectors are singular")

    tokens = lines[5].split()
    if not tokens:
        raise ValueError("POSCAR species/count line is empty")
    old_style = all(re.fullmatch(r"\d+", token) for token in tokens)
    if old_style:
        symbols = None
        counts = [int(token) for token in tokens]
        count_line = 5
    else:
        symbols = tokens
        if len(lines) <= 6:
            raise ValueError("POSCAR atom count line is missing")
        count_tokens = lines[6].split()
        if not count_tokens or not all(re.fullmatch(r"\d+", token) for token in count_tokens):
            raise ValueError("POSCAR atom counts must be non-negative integers")
        counts = [int(token) for token in count_tokens]
        count_line = 6
        if len(symbols) != len(counts):
            raise ValueError("POSCAR species and count lengths differ")
    if sum(counts) <= 0:
        raise ValueError("POSCAR total atom count must be positive")

    coordinate_line = count_line + 1
    if coordinate_line >= len(lines):
        raise ValueError("POSCAR coordinate mode is missing")
    selective = lines[coordinate_line].lower().startswith("s")
    if selective:
        coordinate_line += 1
    if coordinate_line >= len(lines):
        raise ValueError("POSCAR coordinate mode is missing")
    coordinate_mode = lines[coordinate_line]
    if not coordinate_mode or coordinate_mode[0].lower() not in {"d", "c", "k"}:
        raise ValueError(f"POSCAR coordinate mode is not explicitly Direct/Cartesian: {coordinate_mode!r}")

    atom_count = sum(counts)
    coordinate_rows = lines[coordinate_line + 1 : coordinate_line + 1 + atom_count]
    if len(coordinate_rows) != atom_count:
        raise ValueError(f"POSCAR declares {atom_count} atoms but contains {len(coordinate_rows)} coordinate rows")
    seen_coordinates: set[tuple[float, float, float]] = set()
    exact_duplicates = 0
    for offset, row in enumerate(coordinate_rows, start=coordinate_line + 2):
        values = row.split()
        if len(values) < 3:
            raise ValueError(f"POSCAR coordinate line {offset} has fewer than three values")
        coordinates = tuple(finite_float(value, f"POSCAR coordinate line {offset}") for value in values[:3])
        if coordinates in seen_coordinates:
            exact_duplicates += 1
        seen_coordinates.add(coordinates)
        if selective and (len(values) < 6 or any(value.upper() not in {"T", "F"} for value in values[3:6])):
            raise ValueError(f"POSCAR selective-dynamics line {offset} lacks three explicit T/F flags")
    return {
        "sha256": sha256_file(path),
        "scale": scale,
        "raw_lattice_determinant": raw_determinant,
        "symbols": symbols,
        "counts": counts,
        "atom_count": atom_count,
        "selective_dynamics": selective,
        "coordinate_mode": "direct" if coordinate_mode[0].lower() == "d" else "cartesian",
        "coordinate_rows": len(coordinate_rows),
        "exact_duplicate_coordinate_rows": exact_duplicates,
    }


def parse_potcar(path: Path) -> dict[str, Any]:
    titles: list[str] = []
    enmax: list[float] = []
    lexch: list[str] = []
    end_markers = 0
    with path.open(errors="replace") as handle:
        for line in handle:
            if "End of Dataset" in line:
                end_markers += 1
            if "TITEL" in line and "=" in line:
                titles.append(line.split("=", 1)[1].strip())
            match = re.search(r"\bENMAX\s*=\s*([-+0-9.Ee]+)", line)
            if match:
                value = float(match.group(1))
                if math.isfinite(value):
                    enmax.append(value)
            match = re.search(r"\bLEXCH\s*=\s*([^;\s]+)", line)
            if match:
                lexch.append(match.group(1))
    labels: list[str | None] = []
    elements: list[str | None] = []
    for title in titles:
        tokens = title.split()
        label = tokens[1] if len(tokens) > 1 and tokens[0].upper().startswith("PAW") else None
        labels.append(label)
        match = re.match(r"[A-Z][a-z]?", label or "")
        elements.append(match.group(0) if match else None)
    return {
        "sha256": sha256_file(path),
        "datasets": len(titles),
        "end_markers": end_markers,
        "titles": titles,
        "dataset_labels": labels,
        "elements": elements,
        "enmax_ev": enmax,
        "lexch": lexch,
    }


def parse_kpoints(path: Path) -> dict[str, Any]:
    lines = [
        cleaned
        for raw in path.read_text(errors="replace").splitlines()
        if (cleaned := strip_comment(raw).strip())
    ]
    if len(lines) < 3:
        raise ValueError("KPOINTS has fewer than 3 nonempty lines")
    count = strict_integer(lines[1].split()[0], "KPOINTS declared count")
    if count < 0:
        raise ValueError("KPOINTS declared count must be non-negative")
    result: dict[str, Any] = {"sha256": sha256_file(path), "declared_count": count}
    scheme = lines[2]
    if count == 0:
        if len(lines) < 4:
            raise ValueError("automatic KPOINTS is missing its mesh/length line")
        first = scheme[:1].lower()
        if first in {"g", "m"}:
            mesh_tokens = lines[3].split()
            if len(mesh_tokens) != 3:
                raise ValueError("automatic KPOINTS mesh must contain exactly three integers")
            mesh = [strict_integer(token, "automatic KPOINTS mesh") for token in mesh_tokens]
            if any(value <= 0 for value in mesh):
                raise ValueError("automatic KPOINTS mesh values must be positive")
            shift = None
            if len(lines) >= 5:
                shift_tokens = lines[4].split()
                if len(shift_tokens) != 3:
                    raise ValueError("KPOINTS shift must contain exactly three numbers")
                shift = [finite_float(token, "KPOINTS shift") for token in shift_tokens]
            result.update({"mode": "automatic_mesh", "scheme": "gamma" if first == "g" else "monkhorst-pack", "mesh": mesh, "shift": shift})
        elif first == "a":
            length_tokens = lines[3].split()
            if len(length_tokens) != 1:
                raise ValueError("automatic-length KPOINTS must contain one positive number")
            length = finite_float(length_tokens[0], "automatic-length KPOINTS value")
            if length <= 0:
                raise ValueError("automatic-length KPOINTS value must be positive")
            result.update({"mode": "automatic_length", "length": length})
        elif first in {"c", "k", "r"}:
            if len(lines) < 6:
                raise ValueError("generalized automatic KPOINTS requires three generating vectors")
            vectors: list[list[float]] = []
            for row in lines[3:6]:
                tokens = row.split()
                if len(tokens) != 3:
                    raise ValueError("generalized automatic KPOINTS vector must contain three numbers")
                vectors.append([finite_float(token, "generalized automatic KPOINTS vector") for token in tokens])
            shift = None
            if len(lines) >= 7:
                shift_tokens = lines[6].split()
                if len(shift_tokens) != 3:
                    raise ValueError("generalized automatic KPOINTS shift must contain three numbers")
                shift = [finite_float(token, "generalized automatic KPOINTS shift") for token in shift_tokens]
            result.update(
                {
                    "mode": "generalized_automatic",
                    "coordinate_system": "cartesian" if first in {"c", "k"} else "reciprocal",
                    "generating_vectors": vectors,
                    "shift": shift,
                }
            )
        else:
            raise ValueError(f"unsupported automatic KPOINTS scheme: {scheme!r}")
    elif scheme[:1].lower() == "l":
        if len(lines) < 6:
            raise ValueError("line-mode KPOINTS requires coordinate system and at least two points")
        coordinate_system = lines[3]
        coordinate_key = coordinate_system[:1].lower()
        if coordinate_key not in {"c", "f", "k", "r"}:
            raise ValueError("line-mode KPOINTS coordinate system is not explicit Cartesian/Reciprocal")
        point_rows = lines[4:]
        if len(point_rows) < 2:
            raise ValueError("line-mode KPOINTS contains fewer than two points")
        for row in point_rows:
            values = row.split()
            if len(values) < 3:
                raise ValueError("line-mode KPOINTS point has fewer than three coordinates")
            [finite_float(value, "line-mode KPOINTS point") for value in values[:3]]
        result.update(
            {
                "mode": "line",
                "coordinate_system": "cartesian" if coordinate_key in {"c", "k"} else "reciprocal",
                "point_rows": len(point_rows),
            }
        )
    else:
        coordinate_key = scheme[:1].lower()
        if coordinate_key not in {"c", "f", "k", "r"}:
            raise ValueError("explicit KPOINTS coordinate system is not explicit Cartesian/Reciprocal")
        if len(lines) < 3 + count:
            raise ValueError(f"explicit KPOINTS declares {count} points but contains {max(0, len(lines) - 3)}")
        for row in lines[3 : 3 + count]:
            values = row.split()
            if len(values) < 4:
                raise ValueError("explicit KPOINTS row requires three coordinates and a weight")
            [finite_float(value, "explicit KPOINTS row") for value in values[:4]]
        result.update(
            {
                "mode": "explicit",
                "coordinate_system": "cartesian" if coordinate_key in {"c", "k"} else "reciprocal",
                "point_rows": count,
            }
        )
    return result


def warning_category(text: str) -> str:
    lowered = text.casefold()
    patterns = (
        ("very-bad-news", "very bad news"),
        ("brmix", "brmix"),
        ("zbrent", "zbrent"),
        ("edddav", "edddav"),
        ("zhegv", "zhegv"),
        ("subspace-matrix", "sub-space-matrix"),
        ("tetrahedron", "tetrahedron"),
        ("internal-error", "internal error"),
    )
    return next((category for category, marker in patterns if marker in lowered), "unclassified-warning")


def parse_outcar(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "sha256": sha256_file(path),
        "version": None,
        "completed": False,
        "ionic_converged": False,
        "electronic_converged": None,
        "electronic_convergence_basis": "not-observed",
        "encut_ev": None,
        "ediff": None,
        "nelm": None,
        "nkpts": None,
        "ionic_steps": None,
        "warnings": [],
        "stop_markers": [],
        "fatal_markers": [],
    }
    electronic_iterations: dict[int, int] = {}
    explicit_ediff_marker = False
    with path.open(errors="replace") as handle:
        for line_number, raw in enumerate(handle, 1):
            line = raw.strip()
            if result["version"] is None:
                match = re.search(r"\bvasp\.([0-9][^\s]*)", line, re.IGNORECASE)
                if match:
                    result["version"] = match.group(0)
            for key, pattern in (
                ("encut_ev", r"\bENCUT\s*=\s*([-+0-9.Ee]+)"),
                ("ediff", r"\bEDIFF\s*=\s*([-+0-9.Ee]+)"),
            ):
                if result[key] is None:
                    match = re.search(pattern, line)
                    if match:
                        value = float(match.group(1))
                        result[key] = value if math.isfinite(value) else None
            if result["nelm"] is None:
                match = re.search(r"\bNELM\s*=\s*(\d+)", line)
                if match:
                    result["nelm"] = int(match.group(1))
            if result["nkpts"] is None:
                match = re.search(r"\bNKPTS\s*=\s*(\d+)", line)
                if match:
                    result["nkpts"] = int(match.group(1))
            match = re.search(r"\bIteration\s+(\d+)\(\s*(\d+)\)", line)
            if match:
                ionic_step, electronic_step = int(match.group(1)), int(match.group(2))
                electronic_iterations[ionic_step] = max(electronic_iterations.get(ionic_step, 0), electronic_step)
            lowered = line.lower()
            if "aborting loop because ediff is reached" in lowered:
                explicit_ediff_marker = True
            if "reached required accuracy" in lowered:
                result["ionic_converged"] = True
            if "General timing and accounting informations for this job" in line or "Elapsed time (sec)" in line:
                result["completed"] = True
            if "stopcar" in lowered or "soft stop" in lowered:
                if len(result["stop_markers"]) < 20:
                    result["stop_markers"].append(
                        {"sha256": hashlib.sha256(line.encode("utf-8", errors="replace")).hexdigest(), "line": line_number}
                    )
            fatal_category = next(
                (
                    category
                    for category, marker in (
                        ("very-bad-news", "very bad news"),
                        ("internal-error", "internal error in"),
                        ("refuse-to-continue", "refuse to continue"),
                        ("vasp-stopped", "vasp stops"),
                    )
                    if marker in lowered
                ),
                None,
            )
            if fatal_category and len(result["fatal_markers"]) < 20:
                result["fatal_markers"].append(
                    {
                        "sha256": hashlib.sha256(line.encode("utf-8", errors="replace")).hexdigest(),
                        "line": line_number,
                        "category": fatal_category,
                    }
                )
            category = warning_category(line)
            if category != "unclassified-warning" or re.search(r"\bWARNING\b", line, re.IGNORECASE):
                if len(result["warnings"]) < 50:
                    result["warnings"].append(
                        {
                            "sha256": hashlib.sha256(line.encode("utf-8", errors="replace")).hexdigest(),
                            "line": line_number,
                            "category": category,
                            "text_redacted": True,
                        }
                    )
    if electronic_iterations:
        result["ionic_steps"] = max(electronic_iterations)
    if explicit_ediff_marker:
        result["electronic_converged"] = True
        result["electronic_convergence_basis"] = "explicit-ediff-marker"
    elif result["completed"] and result["nelm"] and electronic_iterations:
        exhausted = [step for step, count in electronic_iterations.items() if count >= result["nelm"]]
        result["electronic_converged"] = not exhausted
        result["electronic_convergence_basis"] = "iteration-count-versus-nelm"
        if exhausted:
            result["electronic_steps_at_nelm"] = exhausted[:50]
    return result


def mirror_coverage(tags: dict[str, str]) -> dict[str, Any]:
    try:
        manifest = json.loads(MIRROR_MANIFEST.read_text(encoding="utf-8"))
    except OSError:
        return {"status": "unavailable", "error": "local mirror manifest cannot be read", "covered": {}, "missing": sorted(tags)}
    except json.JSONDecodeError:
        return {"status": "unavailable", "error": "local mirror manifest is invalid JSON", "covered": {}, "missing": sorted(tags)}
    pages = {}
    for record in manifest.get("pages", []):
        title = str(record.get("title", ""))
        keys = {title.upper(), title.removeprefix("Category:").upper()}
        for key in keys:
            pages[key] = record
    covered = {
        tag: {
            "title": pages[tag]["title"],
            "url": pages[tag]["url"],
            "revision": pages[tag]["revid"],
            "local_path": pages[tag]["markdown_path"],
        }
        for tag in sorted(tags)
        if tag in pages
    }
    missing = sorted(set(tags) - set(covered))
    return {
        "status": "pass" if not missing else "partial",
        "retrieved_utc": manifest.get("retrieved_utc"),
        "covered": covered,
        "missing": missing,
        "limitation": "Missing means absent from the local mirror, not absent from the live official VASP Wiki.",
    }


def finding(severity: str, code: str, message: str, basis: str, gate: str) -> dict[str, str]:
    return {"severity": severity, "code": code, "message": message, "basis": basis, "gate": gate}


def summarize(findings: list[dict[str, str]]) -> dict[str, int]:
    return {
        "errors": sum(item["severity"] == "error" for item in findings),
        "warnings": sum(item["severity"] == "warning" for item in findings),
        "info": sum(item["severity"] == "info" for item in findings),
    }


def audit(case: Path, mode: str = "input", task_type: str = "generic") -> dict[str, Any]:
    if mode not in {"input", "run"}:
        raise ValueError("mode must be input or run")
    if task_type not in RUN_TASKS:
        raise ValueError(f"unsupported task type: {task_type}")
    findings: list[dict[str, str]] = []
    result: dict[str, Any] = {
        "audit_schema_version": AUDIT_SCHEMA_VERSION,
        "auditor": "audit_vasp_case.py",
        "mode": mode,
        "task_type": task_type,
        "case_id": "unavailable",
        "files": {},
        "findings": findings,
    }
    if not case.is_dir():
        findings.append(finding("error", "case-not-directory", "Case path is not a directory", "file integrity", "input_integrity"))
        result["summary"] = summarize(findings)
        result["gates"] = {"input_integrity": "fail", "scientific_claim": "blocked"}
        result["verdict"] = "blocked"
        return result

    required = ["INCAR", "POSCAR", "POTCAR"]
    for name in required:
        if not (case / name).is_file():
            findings.append(finding("error", f"missing-{name.lower()}", f"{name} is missing", "file integrity", "input_integrity"))
    if any(not (case / name).is_file() for name in required):
        result["summary"] = summarize(findings)
        result["gates"] = {"input_integrity": "fail", "scientific_claim": "blocked"}
        result["verdict"] = "blocked"
        return result

    tags, duplicates, malformed = parse_incar(case / "INCAR")
    try:
        poscar = parse_poscar(case / "POSCAR")
        potcar = parse_potcar(case / "POTCAR")
    except ValueError as exc:
        findings.append(finding("error", "input-parse-error", str(exc), "input parse", "input_integrity"))
        result["summary"] = summarize(findings)
        result["gates"] = {"input_integrity": "fail", "scientific_claim": "blocked"}
        result["verdict"] = "blocked"
        return result

    input_hashes = [sha256_file(case / "INCAR"), poscar["sha256"], potcar["sha256"]]
    result["case_id"] = "case-" + hashlib.sha256("".join(input_hashes).encode()).hexdigest()[:16]
    result["files"]["INCAR"] = {
        "sha256": input_hashes[0],
        "tag_names": sorted(tags),
        "selected_values": {key: tags[key] for key in sorted(tags) if key in SAFE_VALUE_TAGS},
        "duplicate_tags": duplicates,
        "malformed": malformed,
    }
    result["files"]["POSCAR"] = poscar
    result["files"]["POTCAR"] = potcar
    result["official_source_coverage"] = mirror_coverage(tags)

    for tag in duplicates:
        findings.append(finding("error", "duplicate-incar-tag", f"{tag} is assigned more than once", "input ambiguity", "input_integrity"))
    for item in malformed:
        findings.append(finding("error", "malformed-incar-statement", f"INCAR line {item['line']}: {item['reason']}", "input parse", "input_integrity"))

    parsed_numbers: dict[str, float | int] = {}
    for tag in sorted(FLOAT_TAGS & set(tags)):
        try:
            parsed_numbers[tag] = finite_float(tags[tag], tag)
        except ValueError as exc:
            findings.append(finding("error", "invalid-numeric-tag", str(exc), "input parse", "input_integrity"))
    for tag in sorted(INTEGER_TAGS & set(tags)):
        try:
            parsed_numbers[tag] = strict_integer(tags[tag], tag)
        except ValueError as exc:
            findings.append(finding("error", "invalid-integer-tag", str(exc), "input parse", "input_integrity"))
    for tag in sorted(BOOLEAN_TAGS & set(tags)):
        try:
            logical_value(tags[tag], tag)
        except ValueError as exc:
            findings.append(finding("error", "invalid-logical-tag", str(exc), "input parse", "input_integrity"))

    for positive_tag in ("EDIFF", "ENCUT", "KSPACING"):
        if positive_tag in parsed_numbers and parsed_numbers[positive_tag] <= 0:
            findings.append(finding("error", "nonpositive-numeric-tag", f"{positive_tag} must be positive", "input validity", "input_integrity"))
    for positive_integer_tag in ("NBANDS", "NELM"):
        if positive_integer_tag in parsed_numbers and parsed_numbers[positive_integer_tag] <= 0:
            findings.append(finding("error", "nonpositive-integer-tag", f"{positive_integer_tag} must be positive", "input validity", "input_integrity"))
    if "NSW" in parsed_numbers and parsed_numbers["NSW"] < 0:
        findings.append(finding("error", "negative-nsw", "NSW must be non-negative", "input validity", "input_integrity"))
    if "ISPIN" in parsed_numbers and parsed_numbers["ISPIN"] not in {1, 2}:
        findings.append(finding("error", "invalid-ispin", "ISPIN must be 1 or 2", "input validity", "input_integrity"))

    if potcar["datasets"] == 0:
        findings.append(finding("error", "potcar-metadata-unreadable", "No TITEL metadata was found in POTCAR", "parser limitation or invalid file", "input_integrity"))
    elif potcar["end_markers"] != potcar["datasets"]:
        findings.append(finding("error", "potcar-dataset-boundary-mismatch", f"POTCAR contains {potcar['datasets']} TITEL records but {potcar['end_markers']} dataset end markers", "POTCAR file integrity", "input_integrity"))
    if potcar["enmax_ev"] and len(potcar["enmax_ev"]) != potcar["datasets"]:
        findings.append(finding("warning", "potcar-enmax-count-mismatch", "POTCAR ENMAX metadata count differs from dataset count", "POTCAR metadata completeness", "input_integrity"))
    if potcar["lexch"] and len(potcar["lexch"]) != potcar["datasets"]:
        findings.append(finding("warning", "potcar-lexch-count-mismatch", "POTCAR LEXCH metadata count differs from dataset count", "POTCAR metadata completeness", "input_integrity"))
    if potcar["datasets"] and len(poscar["counts"]) != potcar["datasets"]:
        findings.append(finding("error", "species-potcar-count-mismatch", "POSCAR species count differs from POTCAR dataset count", "input consistency", "input_integrity"))
    elif poscar["symbols"] and potcar["elements"] and all(potcar["elements"]):
        if poscar["symbols"] != potcar["elements"]:
            findings.append(finding("error", "species-potcar-order-mismatch", f"POSCAR species order {poscar['symbols']} differs from POTCAR element order {potcar['elements']}", "input consistency", "input_integrity"))
    if poscar["exact_duplicate_coordinate_rows"]:
        findings.append(finding("error", "duplicate-poscar-coordinates", f"POSCAR contains {poscar['exact_duplicate_coordinate_rows']} exact duplicate coordinate row(s)", "structural integrity", "input_integrity"))

    encut = parsed_numbers.get("ENCUT")
    if encut is None and "ENCUT" not in tags:
        findings.append(finding("warning", "encut-not-explicit", "ENCUT is not explicitly recorded in INCAR", "reproducibility; convergence remains required", "input_integrity"))
    elif isinstance(encut, (int, float)) and potcar["enmax_ev"] and encut < max(potcar["enmax_ev"]):
        findings.append(finding("warning", "encut-below-max-enmax", f"ENCUT={encut:g} eV is below maximum POTCAR ENMAX={max(potcar['enmax_ev']):g} eV", "requires intentional justification and observable-specific convergence evidence", "input_integrity"))

    kpoints_path = case / "KPOINTS"
    if not kpoints_path.is_file() and "KSPACING" not in tags:
        findings.append(finding("error", "sampling-not-specified", "Neither KPOINTS nor KSPACING is present", "input completeness", "input_integrity"))
    elif kpoints_path.is_file():
        try:
            result["files"]["KPOINTS"] = parse_kpoints(kpoints_path)
        except ValueError as exc:
            findings.append(finding("error", "kpoints-parse-error", str(exc), "input parse", "input_integrity"))
        if "KSPACING" in tags:
            findings.append(finding("warning", "kpoints-and-kspacing", "Both KPOINTS and KSPACING are present; verify the documented precedence intentionally", "input ambiguity", "input_integrity"))

    for tag, message in (
        ("EDIFF", "Electronic stopping criterion is not explicit"),
        ("ISMEAR", "Occupation method is not explicit"),
        ("SIGMA", "Occupation broadening is not explicit"),
    ):
        if tag not in tags:
            findings.append(finding("warning", f"{tag.lower()}-not-explicit", message, "reproducibility and observable-specific convergence", "input_integrity"))

    nsw = parsed_numbers.get("NSW", 0)
    ibrion = parsed_numbers.get("IBRION")
    relaxing = isinstance(nsw, int) and nsw > 0 and ibrion != -1 and task_type != "md"
    if task_type == "relax" and not relaxing:
        findings.append(finding("error", "task-profile-mismatch", "Task type relax does not have an active ionic-relaxation setup", "task profile", "input_integrity"))
    if task_type in STATIC_TASKS and relaxing:
        findings.append(finding("error", "task-profile-mismatch", f"Task type {task_type} unexpectedly enables ionic steps", "task profile", "input_integrity"))
    if relaxing and "EDIFFG" not in tags:
        findings.append(finding("warning", "ediffg-not-explicit", "Relaxation detected but EDIFFG is not explicit", "ionic stopping criterion should be recorded", "input_integrity"))
    if relaxing and "ISIF" not in tags:
        findings.append(finding("warning", "isif-not-explicit", "Relaxation detected but ISIF is not explicit", "relaxed degrees of freedom should be recorded", "input_integrity"))

    icharg = parsed_numbers.get("ICHARG")
    if icharg in {1, 5, 11} and not (case / "CHGCAR").is_file():
        findings.append(finding("error", "missing-chgcar", f"ICHARG={icharg} requires CHGCAR for this workflow, but CHGCAR is absent", "restart/workflow integrity", "input_integrity"))
    if icharg == 4 and not (case / "POT").is_file():
        findings.append(finding("error", "missing-pot", "ICHARG=4 requires POT, but POT is absent", "restart/workflow integrity", "input_integrity"))
    if icharg == 5 and not ((case / "GAMMA").is_file() or (case / "vaspgamma.h5").is_file()):
        findings.append(finding("error", "missing-external-occupations", "ICHARG=5 requires GAMMA or vaspgamma.h5", "restart/workflow integrity", "input_integrity"))
    istart = parsed_numbers.get("ISTART")
    if istart in {1, 2} and not (case / "WAVECAR").is_file():
        findings.append(finding("warning", "missing-wavecar", f"ISTART={istart} but WAVECAR is absent; the requested restart cannot be demonstrated", "restart/workflow integrity", "input_integrity"))
    if istart == 3:
        for name in ("WAVECAR", "TMPCAR"):
            if not (case / name).is_file():
                findings.append(finding("error", f"missing-{name.lower()}", f"ISTART=3 requires a valid {name}", "restart/workflow integrity", "input_integrity"))

    try:
        ldau_enabled = logical_value(tags["LDAU"], "LDAU") if "LDAU" in tags else False
    except ValueError:
        ldau_enabled = False
    if ldau_enabled:
        for tag in ("LDAUL", "LDAUU", "LDAUJ"):
            if tag not in tags:
                findings.append(finding("error", "incomplete-dftu-definition", f"LDAU is enabled but {tag} is not explicit", "reproducible model definition", "input_integrity"))
                continue
            try:
                values = numeric_vector(tags[tag], tag, integer=tag == "LDAUL")
                if len(values) != potcar["datasets"]:
                    findings.append(finding("error", "dftu-vector-length-mismatch", f"{tag} has {len(values)} values for {potcar['datasets']} POTCAR datasets", "species/model mapping", "input_integrity"))
            except ValueError as exc:
                findings.append(finding("error", "invalid-dftu-vector", str(exc), "input parse", "input_integrity"))

    if "MAGMOM" in tags:
        try:
            moments = numeric_vector(tags["MAGMOM"], "MAGMOM")
            noncollinear = any(logical_value(tags[tag], tag) for tag in ("LSORBIT", "LNONCOLLINEAR") if tag in tags)
            expected = poscar["atom_count"] * (3 if noncollinear else 1)
            if len(moments) != expected:
                findings.append(finding("warning", "magmom-length-mismatch", f"MAGMOM expands to {len(moments)} values; explicit mapping expects {expected}", "magnetic initialization mapping", "input_integrity"))
        except ValueError as exc:
            findings.append(finding("error", "invalid-magmom", str(exc), "input parse", "input_integrity"))

    outcar: dict[str, Any] | None = None
    outcar_path = case / "OUTCAR"
    if mode == "input":
        if outcar_path.is_file():
            findings.append(finding("info", "output-not-audited", "OUTCAR exists but input mode does not assess run completion", "scope boundary", "execution_completion"))
    elif not outcar_path.is_file():
        findings.append(finding("error", "outcar-missing", "Run mode requires OUTCAR", "execution evidence", "execution_completion"))
    else:
        outcar = parse_outcar(outcar_path)
        result["files"]["OUTCAR"] = outcar
        if not outcar["completed"]:
            findings.append(finding("error", "outcar-incomplete", "OUTCAR lacks final timing/accounting evidence", "execution completion", "execution_completion"))
        if outcar["stop_markers"]:
            findings.append(finding("error", "outcar-stopped", "OUTCAR contains STOPCAR/soft-stop evidence", "execution stop reason", "execution_completion"))
        if outcar["fatal_markers"]:
            findings.append(finding("error", "outcar-fatal-marker", "OUTCAR contains fatal-error evidence", "execution stop reason", "execution_completion"))
        if outcar["electronic_converged"] is not True:
            code = "electronic-convergence-failed" if outcar["electronic_converged"] is False else "electronic-convergence-unresolved"
            findings.append(finding("error", code, "Electronic convergence is not demonstrated for every observed ionic step", "OUTCAR observation", "electronic_convergence"))
        if relaxing and outcar["ionic_converged"] is not True:
            findings.append(finding("error", "ionic-convergence-unresolved", "Relaxation lacks the standard required-accuracy evidence", "OUTCAR observation", "ionic_convergence"))
        if outcar["version"] is None:
            findings.append(finding("warning", "vasp-version-unresolved", "VASP version was not found in OUTCAR", "version/source matching", "execution_completion"))
        if isinstance(encut, (int, float)) and outcar["encut_ev"] is not None and not math.isclose(encut, outcar["encut_ev"], rel_tol=0, abs_tol=1e-8):
            findings.append(finding("error", "encut-input-output-mismatch", "OUTCAR ENCUT differs from INCAR ENCUT", "echoed setting comparison", "execution_completion"))
        if outcar["warnings"]:
            findings.append(finding("warning", "outcar-warnings", f"OUTCAR contains {len(outcar['warnings'])} captured warning line(s)", "output observation", "execution_completion"))

    input_failed = any(item["severity"] == "error" and item["gate"] == "input_integrity" for item in findings)
    input_unresolved = any(item["severity"] == "warning" and item["gate"] == "input_integrity" for item in findings)
    gates: dict[str, str] = {
        "input_integrity": "fail" if input_failed else "pass",
        "input_reproducibility": "unresolved" if input_unresolved else "pass",
        "execution_completion": "not_evaluated",
        "electronic_convergence": "not_evaluated",
        "ionic_convergence": "not_evaluated" if relaxing else "not_applicable",
        "output_warnings": "not_evaluated",
        "version_identity": "not_evaluated",
        "local_official_source_coverage": result["official_source_coverage"]["status"],
        "task_specific_validation": "not_evaluated",
        "numerical_convergence": "not_evaluated_by_single_case",
        "physical_validity": "not_evaluated_by_single_case",
        "scientific_claim": "blocked",
    }
    if mode == "run":
        gates["execution_completion"] = (
            "pass"
            if outcar and outcar["completed"] and not outcar["stop_markers"] and not outcar["fatal_markers"]
            else "fail"
        )
        if outcar:
            gates["electronic_convergence"] = "pass" if outcar["electronic_converged"] is True else ("fail" if outcar["electronic_converged"] is False else "unresolved")
            if relaxing:
                gates["ionic_convergence"] = "pass" if outcar["ionic_converged"] else "unresolved"
            gates["output_warnings"] = "unresolved" if outcar["warnings"] else "pass"
            gates["version_identity"] = "pass" if outcar["version"] else "unresolved"
    technical_run_pass = mode == "run" and all(
        gates[name] in {"pass", "not_applicable"}
        for name in (
            "input_integrity",
            "input_reproducibility",
            "execution_completion",
            "electronic_convergence",
            "ionic_convergence",
            "output_warnings",
            "version_identity",
        )
    )
    if mode == "input" and gates["input_integrity"] == "pass" and gates["input_reproducibility"] == "pass":
        verdict = "input_gates_passed_run_and_science_not_assessed"
    elif mode == "input" and gates["input_integrity"] == "pass":
        verdict = "input_integrity_passed_reproducibility_unresolved"
    elif technical_run_pass:
        verdict = "technical_run_gates_passed_scientific_claim_blocked"
    else:
        verdict = "blocked"
    findings.append(finding("info", "convergence-series-required", "A single case cannot demonstrate numerical convergence or physical validity", "scientific validation", "numerical_convergence"))
    result["gates"] = gates
    result["verdict"] = verdict
    result["summary"] = summarize(findings)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path)
    parser.add_argument("--mode", choices=("input", "run"), required=True, help="Select pre-run input audit or completed-run audit")
    parser.add_argument("--task-type", choices=sorted(RUN_TASKS), required=True)
    parser.add_argument("--pretty", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = audit(args.case, mode=args.mode, task_type=args.task_type)
    except OSError:
        print(json.dumps({"error": "required VASP input cannot be read"}, ensure_ascii=False), file=sys.stderr)
        return 2
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    if result["summary"]["errors"]:
        return 2
    if result["summary"]["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
