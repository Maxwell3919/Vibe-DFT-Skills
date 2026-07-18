#!/usr/bin/env python3
"""Fail-closed audit of a conservative CP2K Quickstep input and run output."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shlex
import sys
from typing import Any, Iterable


AUDITOR_VERSION = "2.0.0"
SKILL_ROOT = Path(__file__).resolve().parent.parent
TASK_PROFILE_PATH = SKILL_ROOT / "references" / "task-evidence-profiles.json"
METHOD_PROFILE_PATH = SKILL_ROOT / "references" / "method-evidence-profiles.json"
SECTION = re.compile(r"^&([A-Za-z][A-Za-z0-9_]*)\b(.*)$")
END = re.compile(r"^&END(?:\s+([A-Za-z][A-Za-z0-9_]*))?\s*$", re.IGNORECASE)
VERSION_LINE = re.compile(r"CP2K\|\s*version string:\s*(CP2K version\s+[^\r\n]+)", re.IGNORECASE)
RUN_TYPE_LINE = re.compile(r"GLOBAL\|\s*Run type\s+([A-Za-z0-9_+-]+)", re.IGNORECASE)
WARNING_COUNT = re.compile(r"The number of warnings for this run is\s*:\s*([0-9]+)", re.IGNORECASE)
FATAL_OUTPUT = re.compile(r"\bABORT\b|\bCPASSERT\b|\*{3}\s+ERROR\b|\bNaN\b")
RUNTIME_ENVIRONMENT_WARNING = re.compile(
    r"A system call failed|performance degradation|help-[A-Za-z0-9_.-]+\.txt|MPI_ABORT|segmentation fault",
    re.IGNORECASE,
)
PROJECT_LINE = re.compile(r"GLOBAL\|\s*Project name\s+(\S+)", re.IGNORECASE)
BASIS_FILE_LINE = re.compile(r"GLOBAL\|\s*Basis set file name\s+(\S+)", re.IGNORECASE)
POTENTIAL_FILE_LINE = re.compile(r"GLOBAL\|\s*Potential file name\s+(\S+)", re.IGNORECASE)
EVIDENCE_ROLE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")


def load_profiles(path: Path) -> dict[str, dict[str, Any]]:
    """Load a checked-in profile document and reject an ambiguous shape."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0" or not isinstance(payload.get("profiles"), dict):
        raise ValueError(f"Unsupported profile document: {path.name}")
    profiles = payload["profiles"]
    if not profiles or any(not isinstance(name, str) or not isinstance(value, dict) for name, value in profiles.items()):
        raise ValueError(f"Invalid profile entries: {path.name}")
    return profiles


TASK_PROFILES = load_profiles(TASK_PROFILE_PATH)
METHOD_PROFILES = load_profiles(METHOD_PROFILE_PATH)
TASK_RUN_TYPES = {
    name: set(profile.get("run_types", [])) or None
    for name, profile in TASK_PROFILES.items()
}
KNOWN_EVIDENCE_ROLES = {
    role
    for profile in TASK_PROFILES.values()
    for role in profile.get("required_run_evidence_roles", [])
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strip_comment(line: str) -> str:
    quote: str | None = None
    escaped = False
    result: list[str] = []
    for character in line:
        if escaped:
            result.append(character)
            escaped = False
            continue
        if character == "\\" and quote:
            result.append(character)
            escaped = True
            continue
        if character in {"'", '"'}:
            if quote == character:
                quote = None
            elif quote is None:
                quote = character
            result.append(character)
            continue
        if character in {"#", "!"} and quote is None:
            break
        result.append(character)
    return "".join(result).strip()


def parse_input(text: str) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    sections: list[dict[str, Any]] = []
    stack: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []

    def add(code: str, message: str) -> None:
        findings.append({"severity": "error", "code": code, "message": message})

    for line_number, raw in enumerate(text.splitlines(), 1):
        line = strip_comment(raw)
        if not line:
            continue
        if line.startswith("@") or "$" in line:
            add("unsupported-preprocessor", f"CP2K preprocessing or variable expansion appears at input line {line_number}")
            continue
        if ";" in line:
            add("unsupported-multiple-statements", f"Multiple statements are not supported at input line {line_number}")
            continue
        end_match = END.fullmatch(line)
        if end_match:
            if not stack:
                add("unmatched-section-end", f"Section end without an open section at input line {line_number}")
                continue
            expected = stack[-1]["name"]
            declared = (end_match.group(1) or expected).upper()
            if declared != expected:
                add("mismatched-section-end", f"Section end mismatch at input line {line_number}")
            stack.pop()
            continue
        section_match = SECTION.match(line)
        if section_match:
            name = section_match.group(1).upper()
            try:
                argument = shlex.split(section_match.group(2).strip(), posix=True)
            except ValueError:
                add("input-tokenization-error", f"Section header cannot be tokenized at input line {line_number}")
                argument = []
            path = tuple([*(item["name"] for item in stack), name])
            record = {"name": name, "path": path, "argument": argument, "keywords": {}}
            sections.append(record)
            stack.append(record)
            continue
        if not stack:
            add("keyword-outside-section", f"Keyword occurs outside a section at input line {line_number}")
            continue
        try:
            tokens = shlex.split(line, posix=True)
        except ValueError:
            add("input-tokenization-error", f"Keyword cannot be tokenized at input line {line_number}")
            continue
        if not tokens:
            continue
        keyword = tokens[0].upper()
        stack[-1]["keywords"].setdefault(keyword, []).append(tokens[1:])
    if stack:
        add("unclosed-section", "One or more CP2K input sections are not closed")
    return sections, findings


def section_records(sections: list[dict[str, Any]], path: tuple[str, ...]) -> list[dict[str, Any]]:
    return [record for record in sections if record["path"] == path]


def path_tuple(value: str) -> tuple[str, ...]:
    return tuple(part.upper() for part in value.split("/") if part)


def evaluate_task_profile(
    sections: list[dict[str, Any]],
    task_type: str,
    run_type: str | None,
    findings: list[dict[str, str]],
) -> tuple[dict[str, Any], str]:
    profile = TASK_PROFILES[task_type]
    errors_before = sum(item["severity"] == "error" for item in findings)
    expected = set(profile.get("run_types", []))
    if task_type == "generic":
        findings.append(
            {
                "severity": "error",
                "code": "unsupported-generic-task-profile",
                "message": "Select an explicit supported task profile; generic cannot receive a positive audit decision",
            }
        )
    elif run_type not in expected:
        findings.append(
            {
                "severity": "error",
                "code": "task-run-type-mismatch",
                "message": f"RUN_TYPE is incompatible with the declared {task_type} task profile",
            }
        )

    for required in profile.get("required_sections", []):
        if not section_records(sections, path_tuple(required)):
            findings.append(
                {
                    "severity": "error",
                    "code": "missing-task-section",
                    "message": f"The {task_type} task profile requires section {required}",
                }
            )
    alternatives = profile.get("required_sections_any", [])
    if alternatives and not any(section_records(sections, path_tuple(value)) for value in alternatives):
        findings.append(
            {
                "severity": "error",
                "code": "missing-task-section-alternative",
                "message": f"The {task_type} task profile requires one of {', '.join(alternatives)}",
            }
        )
    run_type_section = profile.get("run_type_sections", {}).get(run_type)
    if run_type_section and not section_records(sections, path_tuple(run_type_section)):
        findings.append(
            {
                "severity": "error",
                "code": "task-run-type-section-mismatch",
                "message": f"RUN_TYPE {run_type} requires section {run_type_section} for the {task_type} task profile",
            }
        )
    for requirement in profile.get("required_keywords", []):
        section_name, separator, keyword = requirement.partition(":")
        if not separator or not keyword_values(sections, path_tuple(section_name), keyword.upper()):
            findings.append(
                {
                    "severity": "error",
                    "code": "missing-task-keyword",
                    "message": f"The {task_type} task profile requires explicit {requirement}",
                }
            )

    errors_after = sum(item["severity"] == "error" for item in findings)
    safe_profile = {
        "name": task_type,
        "run_audit_maturity": profile.get("run_audit_maturity", "blocked"),
        "required_run_evidence_roles": list(profile.get("required_run_evidence_roles", [])),
        "required_source_topics": list(profile.get("required_source_topics", [])),
        "scientific_dimensions": list(profile.get("scientific_dimensions", [])),
    }
    return safe_profile, "pass" if errors_after == errors_before else "fail"


def detect_method_profiles(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    detected: list[dict[str, Any]] = []
    for name, profile in METHOD_PROFILES.items():
        declared_sections = profile.get("sections", [])
        if declared_sections and any(section_records(sections, path_tuple(value)) for value in declared_sections):
            detected.append(
                {
                    "name": name,
                    "maturity": profile.get("maturity", "blocked"),
                    "source_topics": list(profile.get("source_topics", [])),
                }
            )
    return detected


def keyword_values(sections: list[dict[str, Any]], path: tuple[str, ...], keyword: str) -> list[list[str]]:
    values: list[list[str]] = []
    for record in section_records(sections, path):
        values.extend(record["keywords"].get(keyword, []))
    return values


def single_value(
    sections: list[dict[str, Any]],
    path: tuple[str, ...],
    keyword: str,
    findings: list[dict[str, str]],
    *,
    required: bool = True,
) -> list[str] | None:
    values = keyword_values(sections, path, keyword)
    if not values:
        if required:
            findings.append({"severity": "error", "code": "missing-required-keyword", "message": f"Missing explicit {'/'.join(path)}/{keyword}"})
        return None
    if len(values) != 1:
        findings.append({"severity": "error", "code": "duplicate-keyword", "message": f"Duplicate decisive keyword {'/'.join(path)}/{keyword}"})
        return None
    if not values[0]:
        findings.append({"severity": "error", "code": "missing-keyword-value", "message": f"Missing value for {'/'.join(path)}/{keyword}"})
        return None
    return values[0]


def positive_number(tokens: list[str] | None, label: str, findings: list[dict[str, str]], *, integer: bool = False) -> float | int | None:
    if tokens is None:
        return None
    if len(tokens) != 1:
        findings.append({"severity": "error", "code": "unsupported-unit-or-expression", "message": f"{label} must be one explicit scalar in the deterministic core"})
        return None
    try:
        value = int(tokens[0]) if integer else float(tokens[0].replace("D", "E").replace("d", "e"))
    except ValueError:
        findings.append({"severity": "error", "code": "invalid-numeric-keyword", "message": f"{label} is not a supported numeric scalar"})
        return None
    if not math.isfinite(float(value)) or value <= 0:
        findings.append({"severity": "error", "code": "invalid-numeric-keyword", "message": f"{label} must be finite and positive"})
        return None
    return value


def validate_structure(sections: list[dict[str, Any]], findings: list[dict[str, str]]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    required_single = [
        ("GLOBAL",),
        ("FORCE_EVAL",),
        ("FORCE_EVAL", "DFT"),
        ("FORCE_EVAL", "SUBSYS"),
        ("FORCE_EVAL", "SUBSYS", "CELL"),
        ("FORCE_EVAL", "SUBSYS", "COORD"),
    ]
    for path in required_single:
        count = len(section_records(sections, path))
        if count != 1:
            findings.append({"severity": "error", "code": "section-cardinality", "message": f"Expected exactly one {'/'.join(path)} section"})

    run_type = single_value(sections, ("GLOBAL",), "RUN_TYPE", findings)
    project_name = single_value(sections, ("GLOBAL",), "PROJECT_NAME", findings)
    method = single_value(sections, ("FORCE_EVAL",), "METHOD", findings)
    if run_type:
        safe["run_type"] = run_type[0].upper()
    if project_name:
        safe["project_name_explicit"] = len(project_name) == 1
        if len(project_name) != 1:
            findings.append({"severity": "error", "code": "unsupported-project-name", "message": "PROJECT_NAME must be one explicit token"})
    if method:
        safe["method"] = method[0].upper()
        if safe["method"] not in {"QS", "QUICKSTEP"}:
            findings.append({"severity": "error", "code": "unsupported-force-eval-method", "message": "The deterministic core supports only explicit QS/QUICKSTEP"})

    basis_names = keyword_values(sections, ("FORCE_EVAL", "DFT"), "BASIS_SET_FILE_NAME")
    potential_names = keyword_values(sections, ("FORCE_EVAL", "DFT"), "POTENTIAL_FILE_NAME")
    if not basis_names:
        findings.append({"severity": "error", "code": "missing-data-declaration", "message": "Missing explicit BASIS_SET_FILE_NAME"})
    if not potential_names:
        findings.append({"severity": "error", "code": "missing-data-declaration", "message": "Missing explicit POTENTIAL_FILE_NAME"})
    safe["declared_basis_files"] = sum(len(item) for item in basis_names)
    safe["declared_potential_files"] = sum(len(item) for item in potential_names)

    cutoff = positive_number(single_value(sections, ("FORCE_EVAL", "DFT", "MGRID"), "CUTOFF", findings), "MGRID/CUTOFF", findings)
    rel_cutoff = positive_number(single_value(sections, ("FORCE_EVAL", "DFT", "MGRID"), "REL_CUTOFF", findings), "MGRID/REL_CUTOFF", findings)
    eps_scf = positive_number(single_value(sections, ("FORCE_EVAL", "DFT", "SCF"), "EPS_SCF", findings), "SCF/EPS_SCF", findings)
    max_scf = positive_number(single_value(sections, ("FORCE_EVAL", "DFT", "SCF"), "MAX_SCF", findings), "SCF/MAX_SCF", findings, integer=True)
    safe.update({"cutoff": cutoff, "rel_cutoff": rel_cutoff, "eps_scf": eps_scf, "max_scf": max_scf})

    xc_sections = [record for record in sections if record["path"][:3] == ("FORCE_EVAL", "DFT", "XC") and record["name"] == "XC_FUNCTIONAL"]
    if not xc_sections:
        findings.append({"severity": "error", "code": "missing-xc-functional", "message": "Missing explicit XC_FUNCTIONAL section"})

    cell_periodic = single_value(sections, ("FORCE_EVAL", "SUBSYS", "CELL"), "PERIODIC", findings)
    poisson_periodic = single_value(sections, ("FORCE_EVAL", "DFT", "POISSON"), "PERIODIC", findings)
    if cell_periodic:
        safe["cell_periodic"] = " ".join(cell_periodic).upper()
    if poisson_periodic:
        safe["poisson_periodic"] = " ".join(poisson_periodic).upper()
    if cell_periodic and poisson_periodic and safe["cell_periodic"] != safe["poisson_periodic"]:
        findings.append({"severity": "error", "code": "periodicity-mismatch", "message": "CELL and POISSON periodicity declarations differ"})

    cell = section_records(sections, ("FORCE_EVAL", "SUBSYS", "CELL"))
    if cell:
        has_abc = bool(cell[0]["keywords"].get("ABC"))
        has_vectors = all(cell[0]["keywords"].get(axis) for axis in ("A", "B", "C"))
        if has_abc == has_vectors:
            findings.append({"severity": "error", "code": "cell-definition", "message": "Provide exactly one supported CELL definition: ABC or A/B/C"})

    coord = section_records(sections, ("FORCE_EVAL", "SUBSYS", "COORD"))
    coordinate_rows = 0
    if coord:
        for rows in coord[0]["keywords"].values():
            for row in rows:
                coordinate_rows += 1
                if len(row) < 3:
                    findings.append({"severity": "error", "code": "coordinate-row", "message": "A coordinate row has fewer than three components"})
                    continue
                try:
                    values = [float(value.replace("D", "E").replace("d", "e")) for value in row[:3]]
                except ValueError:
                    findings.append({"severity": "error", "code": "coordinate-row", "message": "A coordinate row contains an unsupported numeric expression"})
                    continue
                if not all(math.isfinite(value) for value in values):
                    findings.append({"severity": "error", "code": "coordinate-row", "message": "A coordinate row contains a non-finite value"})
    if coordinate_rows == 0:
        findings.append({"severity": "error", "code": "missing-coordinates", "message": "No inline coordinates were found in the supported core"})
    safe["coordinate_rows"] = coordinate_rows

    kinds = section_records(sections, ("FORCE_EVAL", "SUBSYS", "KIND"))
    if not kinds:
        findings.append({"severity": "error", "code": "missing-kind", "message": "No KIND sections were found"})
    for record in kinds:
        if len(record["argument"]) != 1:
            findings.append({"severity": "error", "code": "kind-label", "message": "Each KIND must have one explicit label"})
        for keyword in ("BASIS_SET", "POTENTIAL"):
            values = record["keywords"].get(keyword, [])
            if len(values) != 1 or not values[0]:
                findings.append({"severity": "error", "code": "kind-provenance", "message": f"Each KIND must have one explicit {keyword}"})
    safe["kind_count"] = len(kinds)
    return safe


def declared_data_files(sections: list[dict[str, Any]]) -> set[str]:
    names: set[str] = set()
    for keyword in ("BASIS_SET_FILE_NAME", "POTENTIAL_FILE_NAME"):
        for values in keyword_values(sections, ("FORCE_EVAL", "DFT"), keyword):
            names.update(Path(value).name for value in values)
    return names


def input_output_identity(sections: list[dict[str, Any]]) -> dict[str, Any]:
    projects = keyword_values(sections, ("GLOBAL",), "PROJECT_NAME")
    return {
        "project": projects[0][0] if len(projects) == 1 and len(projects[0]) == 1 else None,
        "basis_files": {
            Path(value).name
            for values in keyword_values(sections, ("FORCE_EVAL", "DFT"), "BASIS_SET_FILE_NAME")
            for value in values
        },
        "potential_files": {
            Path(value).name
            for values in keyword_values(sections, ("FORCE_EVAL", "DFT"), "POTENTIAL_FILE_NAME")
            for value in values
        },
    }


def data_evidence(paths: Iterable[Path], declared: set[str], findings: list[dict[str, str]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    by_name: dict[str, Path] = {}
    for path in paths:
        if path.name in by_name:
            findings.append({"severity": "error", "code": "ambiguous-data-evidence", "message": "Two supplied data files have the same basename"})
            continue
        by_name[path.name] = path
    for index, (name, path) in enumerate(sorted(by_name.items()), 1):
        try:
            record = {
                "label": f"data-{index}",
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "matches_declared_name": name in declared,
            }
        except OSError:
            findings.append({"severity": "error", "code": "unreadable-data-evidence", "message": "A supplied basis/potential data file cannot be read"})
            continue
        records.append(record)
    missing = sorted(declared - set(by_name))
    if missing:
        findings.append({"severity": "error", "code": "missing-data-evidence", "message": f"Hash evidence is missing for {len(missing)} declared basis/potential data file(s)"})
    if not declared:
        findings.append({"severity": "error", "code": "missing-data-declaration", "message": "No basis/potential data filenames were declared"})
    return records


def run_evidence(
    evidence_files: Iterable[tuple[str, Path]],
    findings: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], set[str]]:
    """Hash task evidence without emitting host paths or file contents."""
    records: list[dict[str, Any]] = []
    present: set[str] = set()
    for index, (role, path) in enumerate(evidence_files, 1):
        if not EVIDENCE_ROLE.fullmatch(role) or role not in KNOWN_EVIDENCE_ROLES:
            findings.append({"severity": "error", "code": "unknown-evidence-role", "message": "A task evidence role is unknown"})
            continue
        if role == "main-output":
            findings.append(
                {
                    "severity": "error",
                    "code": "reserved-evidence-role",
                    "message": "main-output is supplied with --output and cannot be duplicated as task evidence",
                }
            )
            continue
        if role in present:
            findings.append({"severity": "error", "code": "duplicate-evidence-role", "message": f"Task evidence role {role} was supplied more than once"})
            continue
        try:
            records.append(
                {
                    "label": f"evidence-{index}",
                    "role": role,
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                    "semantic_validation": "not_performed",
                }
            )
            present.add(role)
        except OSError:
            findings.append({"severity": "error", "code": "unreadable-run-evidence", "message": f"Task evidence role {role} cannot be read"})
    return records, present


def inspect_output(
    text: str,
    task_type: str,
    input_run_type: str | None,
    expected_identity: dict[str, Any],
    findings: list[dict[str, str]],
) -> tuple[dict[str, Any], dict[str, str]]:
    version_match = VERSION_LINE.search(text)
    output_run_type = RUN_TYPE_LINE.search(text)
    starts = len(re.findall(r"PROGRAM STARTED AT", text, re.IGNORECASE))
    ends = len(re.findall(r"PROGRAM ENDED AT", text, re.IGNORECASE))
    fatal_count = len(FATAL_OUTPUT.findall(text))
    runtime_environment_warnings = len(RUNTIME_ENVIRONMENT_WARNING.findall(text))
    warning_matches = [int(value) for value in WARNING_COUNT.findall(text)]
    warning_markers = len(re.findall(r"\*{3}\s+WARNING\b", text, re.IGNORECASE))
    scf_not_converged = len(re.findall(r"SCF run NOT converged", text, re.IGNORECASE))
    scf_converged = len(re.findall(r"SCF run converged in", text, re.IGNORECASE))
    energy_records = len(re.findall(r"ENERGY\|\s+Total FORCE_EVAL", text, re.IGNORECASE))
    project_matches = PROJECT_LINE.findall(text)
    output_basis = {Path(value).name for value in BASIS_FILE_LINE.findall(text)}
    output_potential = {Path(value).name for value in POTENTIAL_FILE_LINE.findall(text)}

    if starts != 1 or ends != 1:
        findings.append({"severity": "error", "code": "incoherent-program-boundary", "message": "Expected exactly one CP2K program start and one program end marker"})
    if fatal_count:
        findings.append({"severity": "error", "code": "fatal-output-marker", "message": f"Detected {fatal_count} redacted fatal/non-finite output marker(s)"})
    if runtime_environment_warnings:
        findings.append(
            {
                "severity": "error",
                "code": "runtime-environment-warning",
                "message": f"Detected {runtime_environment_warnings} redacted runtime/MPI warning marker(s)",
            }
        )
    if version_match is None:
        findings.append({"severity": "error", "code": "missing-version-identity", "message": "CP2K version identity is missing from output"})
    if not warning_matches:
        findings.append({"severity": "error", "code": "missing-warning-count", "message": "The final CP2K warning count is missing"})
        warning_count: int | None = None
    else:
        warning_count = warning_matches[-1]
        if warning_count != 0 or warning_markers:
            findings.append({"severity": "error", "code": "output-warnings", "message": f"Output reports {warning_count} warning(s); warning text is redacted"})
    if scf_not_converged:
        findings.append({"severity": "error", "code": "scf-not-converged", "message": f"Detected {scf_not_converged} nonconverged SCF marker(s)"})
    if scf_converged == 0:
        findings.append({"severity": "error", "code": "missing-scf-convergence", "message": "No supported SCF-converged marker was found"})
    if task_type in {"static", "bands", "dos"} and energy_records == 0:
        findings.append({"severity": "error", "code": "missing-energy-record", "message": "No supported total FORCE_EVAL energy record was found"})

    run_type = output_run_type.group(1).upper() if output_run_type else None
    if run_type is None:
        findings.append({"severity": "error", "code": "missing-output-run-type", "message": "Output does not echo the CP2K run type"})
    if input_run_type and run_type and input_run_type != run_type:
        findings.append({"severity": "error", "code": "run-type-echo-mismatch", "message": "Input and output run types differ"})

    project_match = len(project_matches) == 1 and project_matches[0] == expected_identity.get("project")
    basis_match = bool(output_basis) and output_basis == expected_identity.get("basis_files")
    potential_match = bool(output_potential) and output_potential == expected_identity.get("potential_files")
    run_type_match = bool(input_run_type and run_type and input_run_type == run_type)
    if len(project_matches) != 1 or not output_basis or not output_potential:
        findings.append(
            {
                "severity": "error",
                "code": "missing-output-input-identity",
                "message": "Output lacks a unique project, basis-file, or potential-file identity needed to bind it to the input",
            }
        )
    if not (project_match and basis_match and potential_match and run_type_match):
        findings.append(
            {
                "severity": "error",
                "code": "input-output-identity-mismatch",
                "message": "Output project, run type, basis declaration, or potential declaration differs from the audited input",
            }
        )

    task_complete = "not_applicable"
    if task_type == "relax":
        if run_type == "GEO_OPT":
            marker = "GEOMETRY OPTIMIZATION COMPLETED"
        elif run_type == "CELL_OPT":
            marker = "CELL OPTIMIZATION COMPLETED"
        else:
            marker = ""
        task_complete = "pass" if marker and marker.casefold() in text.casefold() else "fail"
        if task_complete == "fail":
            findings.append({"severity": "error", "code": "missing-relax-completion", "message": "Supported relaxation completion marker is missing"})

    gates = {
        "execution_completion": "pass" if starts == 1 and ends == 1 and fatal_count == 0 else "fail",
        "electronic_convergence": "pass" if scf_converged > 0 and scf_not_converged == 0 else "fail",
        "ionic_or_task_completion": task_complete,
        "output_warnings": "pass" if warning_count == 0 and warning_markers == 0 else "fail",
        "version_identity": "pass" if version_match else "fail",
        "input_output_binding": "pass" if project_match and basis_match and potential_match and run_type_match else "fail",
        "runtime_environment": "pass" if runtime_environment_warnings == 0 else "fail",
    }
    summary = {
        "version": version_match.group(1).strip() if version_match else None,
        "run_type": run_type,
        "program_start_markers": starts,
        "program_end_markers": ends,
        "fatal_markers": fatal_count,
        "runtime_environment_warning_markers": runtime_environment_warnings,
        "warning_count": warning_count,
        "warning_markers": warning_markers,
        "scf_converged_markers": scf_converged,
        "scf_not_converged_markers": scf_not_converged,
        "energy_records": energy_records,
        "input_output_identity": {
            "project_match": project_match,
            "run_type_match": run_type_match,
            "basis_files_match": basis_match,
            "potential_files_match": potential_match,
        },
    }
    return summary, gates


def audit(
    input_path: Path,
    *,
    mode: str = "input",
    task_type: str = "generic",
    output_path: Path | None = None,
    data_files: Iterable[Path] = (),
    evidence_files: Iterable[tuple[str, Path]] = (),
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    try:
        input_text = input_path.read_text(encoding="utf-8", errors="replace")
        input_hash = sha256_file(input_path)
        input_size = input_path.stat().st_size
    except OSError:
        input_text = ""
        input_hash = None
        input_size = None
        findings.append({"severity": "error", "code": "unreadable-input", "message": "The CP2K input cannot be read"})

    sections, parse_findings = parse_input(input_text)
    findings.extend(parse_findings)
    safe_settings = validate_structure(sections, findings) if input_text else {}
    run_type = safe_settings.get("run_type")
    task_profile, task_profile_gate = evaluate_task_profile(sections, task_type, run_type, findings)
    detected_methods = detect_method_profiles(sections)
    unresolved_methods = [item for item in detected_methods if item["maturity"] != "deterministic-core"]
    if unresolved_methods:
        findings.append(
            {
                "severity": "error",
                "code": "method-profile-not-deterministically-validated",
                "message": f"Detected {len(unresolved_methods)} method profile(s) outside the deterministic audit core",
            }
        )
    method_profile_gate = "pass" if not unresolved_methods else "not_evaluated"
    data_records = data_evidence(data_files, declared_data_files(sections), findings) if input_text else []
    evidence_records, evidence_roles = run_evidence(evidence_files, findings)

    input_errors = sum(item["severity"] == "error" for item in findings)
    gates: dict[str, str] = {
        "official_source_coverage": "not_evaluated",
        "input_integrity": "pass" if input_errors == 0 else "fail",
        "input_reproducibility": "pass" if input_errors == 0 else "fail",
        "task_profile": task_profile_gate,
        "method_profile": method_profile_gate,
        "evidence_inventory": "not_evaluated" if mode == "input" else "fail",
        "execution_completion": "not_evaluated" if mode == "input" else "fail",
        "electronic_convergence": "not_evaluated" if mode == "input" else "fail",
        "ionic_or_task_completion": "not_evaluated" if mode == "input" else "fail",
        "output_warnings": "not_evaluated" if mode == "input" else "fail",
        "version_identity": "not_evaluated" if mode == "input" else "fail",
        "input_output_binding": "not_evaluated" if mode == "input" else "fail",
        "runtime_environment": "not_evaluated" if mode == "input" else "fail",
        "numerical_convergence": "not_evaluated_by_single_case",
        "task_specific_validation": "not_evaluated",
        "physical_validity": "not_evaluated_by_single_case",
        "scientific_claim": "blocked",
    }

    output_record: dict[str, Any] | None = None
    output_available = False
    if mode == "run":
        if output_path is None:
            findings.append({"severity": "error", "code": "missing-output", "message": "Run mode requires an explicit CP2K output"})
        else:
            try:
                output_text = output_path.read_text(encoding="utf-8", errors="replace")
                output_record = {"sha256": sha256_file(output_path), "bytes": output_path.stat().st_size}
                output_summary, output_gates = inspect_output(
                    output_text, task_type, run_type, input_output_identity(sections), findings
                )
                output_record.update(output_summary)
                gates.update(output_gates)
                output_available = True
            except OSError:
                findings.append({"severity": "error", "code": "unreadable-output", "message": "The CP2K output cannot be read"})

        present_roles = set(evidence_roles)
        if output_available:
            present_roles.add("main-output")
        required_roles = set(task_profile["required_run_evidence_roles"])
        missing_roles = sorted(required_roles - present_roles)
        if missing_roles:
            findings.append(
                {
                    "severity": "error",
                    "code": "missing-run-evidence",
                    "message": f"The {task_type} task profile is missing {len(missing_roles)} required evidence role(s): {', '.join(missing_roles)}",
                }
            )
            gates["evidence_inventory"] = "fail"
        else:
            gates["evidence_inventory"] = "pass"

        if task_profile["run_audit_maturity"] == "evidence-profile":
            gates["ionic_or_task_completion"] = "not_evaluated"
            findings.append(
                {
                    "severity": "error",
                    "code": "task-completion-not-deterministically-validated",
                    "message": f"The {task_type} task has an evidence profile but no deterministic output-completion validator",
                }
            )

    technical_required = ["input_integrity", "input_reproducibility", "task_profile", "method_profile"]
    if mode == "run":
        technical_required.extend(
            [
                "execution_completion",
                "electronic_convergence",
                "output_warnings",
                "version_identity",
                "input_output_binding",
                "runtime_environment",
                "evidence_inventory",
            ]
        )
        if task_type != "static":
            technical_required.append("ionic_or_task_completion")
    decision = "pass" if all(gates.get(name) == "pass" for name in technical_required) else "blocked"
    verdict = (
        "technical_run_gates_passed_scientific_claim_blocked"
        if mode == "run" and decision == "pass"
        else "input_gates_passed_scientific_claim_blocked"
        if mode == "input" and decision == "pass"
        else "blocked"
    )
    error_count = sum(item["severity"] == "error" for item in findings)
    case_seed = input_hash or "missing-input"
    return {
        "audit_schema_version": "1.0",
        "auditor": "audit_cp2k_case.py",
        "auditor_version": AUDITOR_VERSION,
        "mode": mode,
        "task_type": task_type,
        "case_id": f"cp2k-{hashlib.sha256(case_seed.encode()).hexdigest()[:20]}",
        "decision": decision,
        "verdict": verdict,
        "scientific_claim_decision": "blocked",
        "files": {
            "input": {"sha256": input_hash, "bytes": input_size, "safe_settings": safe_settings},
            "external_data": data_records,
            "run_evidence": evidence_records,
            "output": output_record,
        },
        "profiles": {
            "task": task_profile,
            "methods": detected_methods,
        },
        "gates": gates,
        "findings": findings,
        "summary": {"errors": error_count, "warnings": 0, "info": 0},
        "limitations": [
            "The parser supports one conservative Quickstep core and does not evaluate CP2K preprocessing, defaults, or arbitrary unit expressions.",
            "Data-file hashes do not prove that selected basis and pseudopotential entries are scientifically appropriate.",
            "Task evidence roles are hashed inventory labels; semantic validation requires a task-specific adapter or claim-package review.",
            "A single-case audit does not establish numerical convergence, complete multi-replica evidence, physical validity, or scientific acceptance.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--mode", choices=("input", "run"), default="input")
    parser.add_argument("--task-type", choices=tuple(TASK_RUN_TYPES), default="generic")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--data-file", action="append", type=Path, default=[])
    parser.add_argument("--evidence", action="append", default=[], metavar="ROLE=PATH")
    parser.add_argument("--pretty", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    evidence_files: list[tuple[str, Path]] = []
    for value in args.evidence:
        role, separator, path = value.partition("=")
        if not separator or not role or not path:
            raise SystemExit("--evidence must use ROLE=PATH")
        evidence_files.append((role, Path(path)))
    result = audit(
        args.input,
        mode=args.mode,
        task_type=args.task_type,
        output_path=args.output,
        data_files=args.data_file,
        evidence_files=evidence_files,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result["decision"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
