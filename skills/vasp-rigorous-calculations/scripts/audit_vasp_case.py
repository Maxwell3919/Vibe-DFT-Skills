#!/usr/bin/env python3
"""Deterministically audit VASP case integrity without exposing POTCAR contents."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


TRUE_VALUES = {"T", ".TRUE.", "TRUE", "1", "YES", "Y"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strip_comment(text: str) -> str:
    positions = [pos for marker in ("!", "#") if (pos := text.find(marker)) >= 0]
    return text[: min(positions)] if positions else text


def parse_incar(path: Path) -> tuple[dict[str, str], list[str], list[str]]:
    tags: dict[str, str] = {}
    duplicates: list[str] = []
    malformed: list[str] = []
    for line_number, raw in enumerate(path.read_text(errors="replace").splitlines(), 1):
        cleaned = strip_comment(raw).strip()
        if not cleaned:
            continue
        for statement in cleaned.split(";"):
            statement = statement.strip()
            if not statement:
                continue
            if "=" not in statement:
                malformed.append(f"line {line_number}: {statement}")
                continue
            key, value = statement.split("=", 1)
            key = key.strip().upper()
            value = value.strip()
            if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key) or not value:
                malformed.append(f"line {line_number}: {statement}")
                continue
            if key in tags:
                duplicates.append(key)
            tags[key] = value
    return tags, sorted(set(duplicates)), malformed


def first_number(value: str | None, kind: type = float) -> Any:
    if value is None:
        return None
    match = re.search(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?", value)
    if not match:
        return None
    try:
        return kind(float(match.group(0))) if kind is int else kind(match.group(0))
    except ValueError:
        return None


def is_true(value: str | None) -> bool:
    return value is not None and value.strip().upper().split()[0] in TRUE_VALUES


def parse_poscar(path: Path) -> dict[str, Any]:
    lines = [line.strip() for line in path.read_text(errors="replace").splitlines()]
    if len(lines) < 8:
        raise ValueError("POSCAR has fewer than 8 lines")
    scale_tokens = lines[1].split()
    if len(scale_tokens) not in {1, 3}:
        raise ValueError("POSCAR scale line must contain one or three numbers")
    try:
        scale = [float(token) for token in scale_tokens]
    except ValueError as exc:
        raise ValueError("POSCAR scale line is not numeric") from exc
    lattice: list[list[float]] = []
    for index in range(2, 5):
        tokens = lines[index].split()
        if len(tokens) != 3:
            raise ValueError(f"POSCAR lattice vector line {index + 1} must contain three numbers")
        try:
            lattice.append([float(token) for token in tokens])
        except ValueError as exc:
            raise ValueError(f"POSCAR lattice vector line {index + 1} is not numeric") from exc
    tokens = lines[5].split()
    if not tokens:
        raise ValueError("POSCAR species/count line is empty")
    old_style = all(re.fullmatch(r"\d+", token) for token in tokens)
    try:
        if old_style:
            symbols = None
            counts = [int(token) for token in tokens]
            count_line = 5
        else:
            symbols = tokens
            count_tokens = lines[6].split()
            if not count_tokens or not all(re.fullmatch(r"\d+", token) for token in count_tokens):
                raise ValueError("POSCAR atom counts must be non-negative integers")
            counts = [int(token) for token in count_tokens]
            count_line = 6
            if len(symbols) != len(counts):
                raise ValueError("POSCAR species and count lengths differ")
    except (IndexError, ValueError) as exc:
        raise ValueError(str(exc)) from exc
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
        raise ValueError(f"POSCAR coordinate mode is invalid: {coordinate_mode!r}")
    atom_count = sum(counts)
    coordinate_rows = lines[coordinate_line + 1 : coordinate_line + 1 + atom_count]
    if len(coordinate_rows) != atom_count:
        raise ValueError(f"POSCAR declares {atom_count} atoms but contains {len(coordinate_rows)} coordinate rows")
    for offset, row in enumerate(coordinate_rows, start=coordinate_line + 2):
        values = row.split()
        if len(values) < 3:
            raise ValueError(f"POSCAR coordinate line {offset} has fewer than three values")
        try:
            [float(value) for value in values[:3]]
        except ValueError as exc:
            raise ValueError(f"POSCAR coordinate line {offset} is not numeric") from exc
        if selective:
            if len(values) < 6 or any(value[:1].upper() not in {"T", "F"} for value in values[3:6]):
                raise ValueError(f"POSCAR selective-dynamics line {offset} lacks three T/F flags")
    return {
        "comment": lines[0],
        "scale": scale,
        "lattice": lattice,
        "symbols": symbols,
        "counts": counts,
        "atom_count": atom_count,
        "selective_dynamics": selective,
        "coordinate_mode": coordinate_mode,
        "coordinate_rows": len(coordinate_rows),
    }


def parse_potcar(path: Path) -> dict[str, Any]:
    titles: list[str] = []
    enmax: list[float] = []
    lexch: list[str] = []
    for line in path.read_text(errors="replace").splitlines():
        if "TITEL" in line and "=" in line:
            titles.append(line.split("=", 1)[1].strip())
        match = re.search(r"\bENMAX\s*=\s*([-+0-9.Ee]+)", line)
        if match:
            enmax.append(float(match.group(1)))
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
        "titles": titles,
        "dataset_labels": labels,
        "elements": elements,
        "enmax_ev": enmax,
        "lexch": lexch,
    }


def parse_kpoints(path: Path) -> dict[str, Any]:
    lines = [line.strip() for line in path.read_text(errors="replace").splitlines() if line.strip()]
    if len(lines) < 3:
        raise ValueError("KPOINTS has fewer than 3 nonempty lines")
    count_token = lines[1].split()[0]
    if not re.fullmatch(r"[+-]?\d+", count_token):
        raise ValueError("KPOINTS declared count is not an integer")
    count = int(count_token)
    if count < 0:
        raise ValueError("KPOINTS declared count must be non-negative")
    result: dict[str, Any] = {"comment": lines[0], "declared_count": count}
    scheme = lines[2]
    result["scheme"] = scheme
    if count == 0:
        if len(lines) < 4:
            raise ValueError("automatic KPOINTS is missing its mesh/length line")
        first = scheme[:1].lower()
        if first in {"g", "m"}:
            mesh_tokens = lines[3].split()
            if len(mesh_tokens) != 3 or not all(re.fullmatch(r"[+-]?\d+", token) for token in mesh_tokens):
                raise ValueError("automatic KPOINTS mesh must contain exactly three integers")
            mesh = [int(token) for token in mesh_tokens]
            if any(value <= 0 for value in mesh):
                raise ValueError("automatic KPOINTS mesh values must be positive")
            shift = None
            if len(lines) >= 5:
                shift_tokens = lines[4].split()
                if len(shift_tokens) != 3:
                    raise ValueError("KPOINTS shift must contain exactly three numbers")
                try:
                    shift = [float(token) for token in shift_tokens]
                except ValueError as exc:
                    raise ValueError("KPOINTS shift is not numeric") from exc
            result.update({"mode": "automatic_mesh", "mesh": mesh, "shift": shift})
        elif first == "a":
            length_tokens = lines[3].split()
            if len(length_tokens) != 1:
                raise ValueError("automatic-length KPOINTS must contain one positive number")
            try:
                length = float(length_tokens[0])
            except ValueError as exc:
                raise ValueError("automatic-length KPOINTS value is not numeric") from exc
            if length <= 0:
                raise ValueError("automatic-length KPOINTS value must be positive")
            result.update({"mode": "automatic_length", "length": length})
        else:
            raise ValueError(f"unsupported automatic KPOINTS scheme: {scheme!r}")
    elif scheme[:1].lower() == "l":
        if len(lines) < 6:
            raise ValueError("line-mode KPOINTS requires coordinate system and at least two points")
        point_rows = [line for line in lines[4:] if line]
        if len(point_rows) < 2:
            raise ValueError("line-mode KPOINTS contains fewer than two points")
        for row in point_rows:
            values = row.split()
            if len(values) < 3:
                raise ValueError("line-mode KPOINTS point has fewer than three coordinates")
            try:
                [float(value) for value in values[:3]]
            except ValueError as exc:
                raise ValueError("line-mode KPOINTS point is not numeric") from exc
        result.update({"mode": "line", "coordinate_system": lines[3], "point_rows": len(point_rows)})
    else:
        if len(lines) < 3 + count:
            raise ValueError(f"explicit KPOINTS declares {count} points but contains {max(0, len(lines) - 3)}")
        for row in lines[3 : 3 + count]:
            values = row.split()
            if len(values) < 4:
                raise ValueError("explicit KPOINTS row requires three coordinates and a weight")
            try:
                [float(value) for value in values[:4]]
            except ValueError as exc:
                raise ValueError("explicit KPOINTS row is not numeric") from exc
        result.update({"mode": "explicit", "point_rows": count})
    return result


def parse_outcar(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "version": None,
        "completed": False,
        "ionic_converged": False,
        "encut_ev": None,
        "nkpts": None,
        "warnings": [],
    }
    for raw in path.read_text(errors="replace").splitlines():
        line = raw.strip()
        if result["version"] is None:
            match = re.search(r"\bvasp\.([0-9][^\s]*)", line, re.IGNORECASE)
            if match:
                result["version"] = match.group(0)
        if result["encut_ev"] is None:
            match = re.search(r"\bENCUT\s*=\s*([-+0-9.Ee]+)", line)
            if match:
                result["encut_ev"] = float(match.group(1))
        if result["nkpts"] is None:
            match = re.search(r"\bNKPTS\s*=\s*(\d+)", line)
            if match:
                result["nkpts"] = int(match.group(1))
        if "reached required accuracy" in line.lower():
            result["ionic_converged"] = True
        if "General timing and accounting informations for this job" in line or "Elapsed time (sec)" in line:
            result["completed"] = True
        if "VERY BAD NEWS" in line or re.search(r"\bWARNING\b", line, re.IGNORECASE):
            if len(result["warnings"]) < 50:
                result["warnings"].append(line[:500])
    return result


def finding(severity: str, code: str, message: str, basis: str) -> dict[str, str]:
    return {"severity": severity, "code": code, "message": message, "basis": basis}


def audit(case: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    result: dict[str, Any] = {
        "case": str(case.resolve()),
        "files": {},
        "findings": findings,
        "scientific_status": "not_demonstrated_by_single_case",
    }
    if not case.is_dir():
        findings.append(finding("error", "case-not-directory", "Case path is not a directory", "file integrity"))
        result["summary"] = {"errors": 1, "warnings": 0, "info": 0}
        return result

    required = ["INCAR", "POSCAR", "POTCAR"]
    for name in required:
        if not (case / name).is_file():
            findings.append(finding("error", f"missing-{name.lower()}", f"{name} is missing", "file integrity"))
    if any(not (case / name).is_file() for name in required):
        result["summary"] = summarize(findings)
        return result

    tags, duplicates, malformed = parse_incar(case / "INCAR")
    poscar = parse_poscar(case / "POSCAR")
    potcar = parse_potcar(case / "POTCAR")
    result["files"]["INCAR"] = {"tags": tags, "duplicate_tags": duplicates, "malformed": malformed}
    result["files"]["POSCAR"] = poscar
    result["files"]["POTCAR"] = potcar

    for tag in duplicates:
        findings.append(finding("warning", "duplicate-incar-tag", f"{tag} is assigned more than once; last value parsed", "input ambiguity"))
    for item in malformed:
        findings.append(finding("warning", "malformed-incar-statement", item, "input parse"))

    if potcar["datasets"] and len(poscar["counts"]) != potcar["datasets"]:
        findings.append(finding("error", "species-potcar-count-mismatch", "POSCAR species count differs from POTCAR dataset count", "input consistency"))
    elif poscar["symbols"] and potcar["elements"] and all(potcar["elements"]):
        if poscar["symbols"] != potcar["elements"]:
            findings.append(
                finding(
                    "error",
                    "species-potcar-order-mismatch",
                    f"POSCAR species order {poscar['symbols']} differs from POTCAR element order {potcar['elements']}",
                    "input consistency",
                )
            )
    if not potcar["titles"]:
        findings.append(finding("warning", "potcar-metadata-unreadable", "No TITEL metadata was found in POTCAR", "parser limitation or invalid file"))

    encut = first_number(tags.get("ENCUT"))
    if encut is None:
        findings.append(finding("warning", "encut-not-explicit", "ENCUT is not explicitly recorded in INCAR", "official Wiki recommends explicit ENCUT for comparable accuracy; convergence remains required"))
    elif potcar["enmax_ev"] and encut < max(potcar["enmax_ev"]):
        findings.append(finding("warning", "encut-below-max-enmax", f"ENCUT={encut:g} eV is below maximum POTCAR ENMAX={max(potcar['enmax_ev']):g} eV", "requires intentional justification and observable-specific convergence evidence"))

    if not (case / "KPOINTS").is_file() and "KSPACING" not in tags:
        findings.append(finding("error", "sampling-not-specified", "Neither KPOINTS nor KSPACING is present", "input completeness"))
    elif (case / "KPOINTS").is_file():
        try:
            result["files"]["KPOINTS"] = parse_kpoints(case / "KPOINTS")
        except ValueError as exc:
            findings.append(finding("error", "kpoints-parse-error", str(exc), "input parse"))

    if "EDIFF" not in tags:
        findings.append(finding("info", "ediff-defaulted", "EDIFF is not explicit", "reproducibility and observable-specific electronic convergence"))
    if "ISMEAR" not in tags:
        findings.append(finding("info", "ismear-defaulted", "ISMEAR is not explicit", "occupation method should be intentional and documented"))
    if "SIGMA" not in tags:
        findings.append(finding("info", "sigma-defaulted", "SIGMA is not explicit", "occupation broadening should be intentional when relevant"))

    nsw = first_number(tags.get("NSW"), int) or 0
    ibrion = first_number(tags.get("IBRION"), int)
    relaxing = nsw > 0 and ibrion != -1
    if relaxing and "EDIFFG" not in tags:
        findings.append(finding("warning", "ediffg-not-explicit", "Relaxation detected but EDIFFG is not explicit", "ionic stopping criterion should be recorded"))
    if relaxing and "ISIF" not in tags:
        findings.append(finding("info", "isif-defaulted", "Relaxation detected but ISIF is not explicit", "relaxed degrees of freedom should be recorded"))

    icharg = first_number(tags.get("ICHARG"), int)
    if icharg in {1, 5, 11} and not (case / "CHGCAR").is_file():
        findings.append(finding("error", "missing-chgcar", f"ICHARG={icharg} reads its initial charge density from CHGCAR, but CHGCAR is absent", "official ICHARG behavior and workflow integrity"))
    if icharg == 4 and not (case / "POT").is_file():
        findings.append(finding("error", "missing-pot", "ICHARG=4 reads the local potential from POT, but POT is absent", "official ICHARG behavior and workflow integrity"))
    if icharg == 5 and not ((case / "GAMMA").is_file() or (case / "vaspgamma.h5").is_file()):
        findings.append(finding("error", "missing-external-occupations", "ICHARG=5 requires GAMMA or vaspgamma.h5 for external occupations", "official ICHARG behavior and workflow integrity"))
    istart = first_number(tags.get("ISTART"), int)
    if istart in {1, 2} and not (case / "WAVECAR").is_file():
        findings.append(finding("warning", "missing-wavecar", f"ISTART={istart} but WAVECAR is absent; official documentation says VASP reverts to ISTART=0", "official ISTART behavior and workflow integrity"))
    if istart == 3:
        for name in ("WAVECAR", "TMPCAR"):
            if not (case / name).is_file():
                findings.append(finding("error", f"missing-{name.lower()}", f"ISTART=3 requires a valid {name}", "official ISTART behavior and workflow integrity"))

    if is_true(tags.get("LDAU")):
        missing = [tag for tag in ("LDAUL", "LDAUU", "LDAUJ") if tag not in tags]
        if missing:
            findings.append(finding("warning", "implicit-dftu-parameters", f"LDAU is enabled but {', '.join(missing)} is not explicit", "defaults may be syntactically valid, but the model definition is not reproducibly explicit"))

    outcar_path = case / "OUTCAR"
    if outcar_path.is_file():
        outcar = parse_outcar(outcar_path)
        result["files"]["OUTCAR"] = outcar
        if not outcar["completed"]:
            findings.append(finding("error", "outcar-incomplete", "OUTCAR lacks final timing/accounting evidence", "execution completion"))
        if relaxing and outcar["completed"] and not outcar["ionic_converged"]:
            findings.append(finding("warning", "ionic-convergence-unconfirmed", "Completed OUTCAR lacks the standard required-accuracy message", "output observation; inspect final forces, stress, and stop reason"))
        if outcar["warnings"]:
            findings.append(finding("warning", "outcar-warnings", f"OUTCAR contains {len(outcar['warnings'])} captured warning line(s)", "output observation"))
    else:
        findings.append(finding("info", "outcar-absent", "No OUTCAR was available; execution and actual settings were not audited", "scope limitation"))

    findings.append(finding("info", "convergence-series-required", "A single case cannot demonstrate numerical convergence or physical validity", "scientific validation"))
    result["summary"] = summarize(findings)
    return result


def summarize(findings: list[dict[str, str]]) -> dict[str, int]:
    return {
        "errors": sum(item["severity"] == "error" for item in findings),
        "warnings": sum(item["severity"] == "warning" for item in findings),
        "info": sum(item["severity"] == "info" for item in findings),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--fail-on-warning", action="store_true")
    args = parser.parse_args()
    try:
        result = audit(args.case)
    except (OSError, ValueError) as exc:
        print(json.dumps({"case": str(args.case), "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    if result["summary"]["errors"]:
        return 2
    if args.fail_on_warning and result["summary"]["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
