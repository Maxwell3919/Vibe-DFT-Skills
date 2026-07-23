#!/usr/bin/env python3
"""Fail-closed, evidence-bound audit for the documented SIESTA 5.4.2 core."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any
from xml.etree import ElementTree

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from create_siesta_plan import normalize_version, validate_plan


TOOL_VERSION = "2.1.0"
SCHEMA_VERSION = "2.0"
SKILL_ROOT = SCRIPT_DIR.parent
REFERENCES = SKILL_ROOT / "references"
OFFICIAL_INDEX = REFERENCES / "official-fdf-index.json"
OFFICIAL_SUPPLEMENTS = REFERENCES / "official-source-supplements.json"
TASK_PROFILES = REFERENCES / "task-evidence-profiles.json"
PSEUDO_SUFFIXES = (".vps", ".psf", ".psml")
ALL_TASKS = ("scf", "relax", "md", "bands", "dos", "phonon", "transiesta", "tbtrans", "optics", "tddft", "generic")
PERIODICITIES = ("molecule", "wire", "slab", "bulk")
PRIVATE_PATH = re.compile(r"(?:/Users/|/home/|[A-Za-z]:\\)")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
FLOAT_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][-+]?\d+)?"
PLACEHOLDERS = {"", "unknown", "unresolved", "none", "n/a", "not_assessed", "not-assessed"}


def generated_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", label.casefold())


def official_key(label: str) -> str:
    return re.sub(r"[^a-z0-9?]+", "", label.casefold())


def digest(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def psml_xc_identity(path: Path) -> dict[str, Any] | None:
    """Read the XC identity embedded in a PSML file without trusting its manifest."""
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError):
        return None
    names: list[str] = []
    ids: list[int] = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1].casefold() != "functional":
            continue
        name = str(element.attrib.get("name", "")).strip()
        if name:
            names.append(name)
        try:
            ids.append(int(element.attrib["id"]))
        except (KeyError, TypeError, ValueError):
            pass
    id_set = set(ids)
    canonical_names = canonical(" ".join(names))
    family = None
    if {101, 130}.issubset(id_set) or "perdewburkeernzerhof" in canonical_names:
        family = "GGA-PBE"
    elif {1, 12}.issubset(id_set) or "pw92" in canonical_names:
        family = "LDA-PW92"
    return {"family": family, "functional_ids": sorted(id_set)}


def xc_family_class(value: str) -> str:
    normalized = canonical(value)
    if "pbesol" in normalized:
        return "pbesol"
    if "pbe" in normalized:
        return "pbe"
    if "pw92" in normalized or "lda" in normalized:
        return "lda-pw92"
    return normalized


def load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not readable JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def resolved_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip().casefold() not in PLACEHOLDERS and not PRIVATE_PATH.search(value)


def strip_comment(line: str) -> str:
    quote: str | None = None
    result: list[str] = []
    for char in line:
        if quote:
            result.append(char)
            if char == quote:
                quote = None
        elif char in {"'", '"'}:
            quote = char
            result.append(char)
        elif char in {"#", "!"}:
            break
        else:
            result.append(char)
    return "".join(result)


def normalized_fdf_lines(text: str) -> list[str]:
    return [" ".join(clean.split()) for line in text.splitlines() if (clean := strip_comment(line).strip())]


def parse_fdf_text(text: str) -> tuple[dict[str, list[str]], dict[str, list[list[str]]], dict[str, str], list[dict[str, str]]]:
    scalars: dict[str, list[str]] = {}
    blocks: dict[str, list[list[str]]] = {}
    labels: dict[str, str] = {}
    findings: list[dict[str, str]] = []
    lines = text.splitlines()
    index = 0

    def add(code: str, message: str) -> None:
        findings.append({"gate": "fdf_syntax", "severity": "error", "code": code, "message": message})

    while index < len(lines):
        raw = strip_comment(lines[index]).strip()
        index += 1
        if not raw:
            continue
        lowered = raw.casefold()
        if lowered.startswith("%include") or "<" in raw:
            add("FDF_EXTERNAL_INPUT_UNSUPPORTED", "External includes and FDF redirection are not expanded by this direct-input profile.")
            continue
        if lowered.startswith("%block"):
            parts = raw.split()
            if len(parts) != 2:
                add("FDF_BLOCK_HEADER_INVALID", "A block header must contain exactly one label.")
                continue
            label = canonical(parts[1])
            labels[label] = parts[1]
            rows: list[list[str]] = []
            closed = False
            while index < len(lines):
                inner = strip_comment(lines[index]).strip()
                index += 1
                if not inner:
                    continue
                if inner.casefold().startswith("%endblock"):
                    end_parts = inner.split()
                    if len(end_parts) > 2 or (len(end_parts) == 2 and canonical(end_parts[1]) != label):
                        add("FDF_BLOCK_END_MISMATCH", "The block closing label differs from its opening label.")
                    closed = True
                    break
                if inner.startswith("%") or "<" in inner:
                    add("FDF_NESTED_DIRECTIVE_UNSUPPORTED", "A block contains an unsupported directive or redirection.")
                    continue
                rows.append(inner.split())
            if not closed:
                add("FDF_BLOCK_UNCLOSED", "A block is missing its %endblock line.")
            if label in blocks or label in scalars:
                add("FDF_DUPLICATE_LABEL", f"Canonical FDF label {label} occurs more than once.")
            else:
                blocks[label] = rows
            continue
        if raw.startswith("%"):
            add("FDF_DIRECTIVE_UNSUPPORTED", "An unsupported FDF directive was found.")
            continue
        parts = raw.split()
        if len(parts) < 2:
            add("FDF_SCALAR_INVALID", "A scalar FDF entry has no value.")
            continue
        label = canonical(parts[0])
        labels[label] = parts[0]
        if label in scalars or label in blocks:
            add("FDF_DUPLICATE_LABEL", f"Canonical FDF label {label} occurs more than once.")
        else:
            scalars[label] = parts[1:]
    return scalars, blocks, labels, findings


def parse_fdf(path: Path) -> tuple[dict[str, list[str]], dict[str, list[list[str]]], dict[str, str], list[dict[str, str]]]:
    return parse_fdf_text(path.read_text(encoding="utf-8", errors="strict"))


def as_float(value: Any) -> float | None:
    try:
        result = float(str(value).replace("D", "E").replace("d", "e"))
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def as_int(tokens: list[str] | None) -> int | None:
    if not tokens or len(tokens) != 1:
        return None
    try:
        return int(tokens[0])
    except ValueError:
        return None


def quantity(tokens: list[str] | None, *, positive: bool = True, require_unit: bool = True) -> tuple[float, str] | None:
    if not tokens or (require_unit and len(tokens) < 2):
        return None
    value = as_float(tokens[0])
    if value is None or (positive and value <= 0):
        return None
    unit = " ".join(tokens[1:]) if len(tokens) > 1 else "dimensionless"
    return value, unit


def truth_value(tokens: list[str] | None) -> bool | None:
    if not tokens or len(tokens) != 1:
        return None
    value = tokens[0].casefold().strip(". ")
    if value in {"true", "t", "yes", "y", "1"}:
        return True
    if value in {"false", "f", "no", "n", "0"}:
        return False
    return None


def matrix_determinant(matrix: list[list[int]]) -> int:
    a, b, c = matrix
    return a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0]) + a[2] * (b[0] * c[1] - b[1] * c[0])


def pattern_matches(key: str, pattern: str) -> bool:
    normalized = official_key(pattern)
    expression = "^" + re.escape(normalized).replace(r"\?", ".+") + "$"
    return re.fullmatch(expression, key) is not None


def load_reference_contracts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    index = load_object(OFFICIAL_INDEX, "official FDF index")
    supplements = load_object(OFFICIAL_SUPPLEMENTS, "official source supplements")
    profiles = load_object(TASK_PROFILES, "task evidence profiles")
    if (
        index.get("schema_version") != "1.0"
        or index.get("code") != "siesta"
        or index.get("entry_count") != len(index.get("entries", []))
        or index.get("source_file_count") != len(index.get("source_files", []))
        or supplements.get("schema_version") != "1.0"
        or supplements.get("source_commit") != index.get("source_commit")
        or profiles.get("schema_version") != "1.0"
        or not isinstance(profiles.get("profiles"), dict)
    ):
        raise ValueError("bundled SIESTA reference contracts are internally inconsistent")
    return index, supplements, profiles


def validate_label_surface(
    labels: dict[str, str], task_type: str, index: dict[str, Any], supplements: dict[str, Any], profiles: dict[str, Any]
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    entries = index["entries"]
    official_patterns = [entry["label"] for entry in entries]
    official_patterns.extend(record["label"] for record in supplements["records"] if record.get("kind") == "fdf-source-definition")
    ambiguous = set(index.get("ambiguous_lookup_keys", []))
    profile = profiles["profiles"].get(task_type, {})
    allowed_patterns = [*profiles["common"]["automated_labels"], *profile.get("extra_automated_labels", [])]
    for key, original in sorted(labels.items()):
        if key in ambiguous:
            findings.append({"gate": "official_source_resolution", "severity": "error", "code": "FDF_LABEL_OFFICIAL_AMBIGUITY", "message": f"{original} has multiple official source definitions and needs context-specific review."})
        elif not any(pattern_matches(key, pattern) for pattern in official_patterns):
            findings.append({"gate": "official_source_resolution", "severity": "error", "code": "FDF_LABEL_NOT_IN_PINNED_INDEX", "message": f"{original} is absent from the pinned 5.4.2 manual/source index."})
        elif not any(pattern_matches(key, pattern) for pattern in allowed_patterns):
            findings.append({"gate": "fdf_semantics", "severity": "error", "code": "FDF_LABEL_NOT_AUTOMATED", "message": f"{original} is official but outside the automated {task_type} profile."})
    return findings


def extract_echo(text: str) -> list[str] | None:
    matches = list(re.finditer(r"^\*+\s*Dump of input data file\s*\*+\s*$", text, re.IGNORECASE | re.MULTILINE))
    ends = list(re.finditer(r"^\*+\s*End of input data file\s*\*+\s*$", text, re.IGNORECASE | re.MULTILINE))
    if len(matches) != 1 or len(ends) != 1 or ends[0].start() <= matches[0].end():
        return None
    return normalized_fdf_lines(text[matches[0].end() : ends[0].start()])


def parse_force_block(text: str) -> tuple[float | None, int]:
    headers = list(re.finditer(r"^\s*siesta:\s+Atomic forces \(eV/Ang\):\s*$", text, re.IGNORECASE | re.MULTILINE))
    if not headers:
        return None, 0
    tail = text[headers[-1].end() :]
    forces: list[float] = []
    row_re = re.compile(rf"^\s*(?:siesta:\s*)?(\d+)\s+({FLOAT_RE})\s+({FLOAT_RE})\s+({FLOAT_RE})\s*$", re.IGNORECASE)
    for line in tail.splitlines():
        if not line.strip() and not forces:
            continue
        match = row_re.fullmatch(line)
        if match is None:
            if forces:
                break
            continue
        vector = [as_float(match.group(i)) for i in range(2, 5)]
        if any(value is None for value in vector):
            continue
        forces.append(math.sqrt(sum(float(value) ** 2 for value in vector)))
    return (max(forces) if forces else None), len(forces)


def parse_output_text(text: str) -> dict[str, Any]:
    versions = re.findall(r"^\s*(?:Siesta\s+)?Version\s*:\s*(\S+)", text, re.IGNORECASE | re.MULTILINE)
    starts = len(re.findall(r"^\s*>>\s*Start of run\s*:", text, re.IGNORECASE | re.MULTILINE))
    ends = len(re.findall(r"^\s*>>\s*End of run\s*:", text, re.IGNORECASE | re.MULTILINE))
    completions = len(re.findall(r"^\s*Job\s+completed\s*$", text, re.IGNORECASE | re.MULTILINE))
    scf_iterations = [int(value) for value in re.findall(r"SCF\s+cycle\s+converged\s+after\s+(\d+)\s+iterations", text, re.IGNORECASE)]
    total_values = [as_float(value) for value in re.findall(rf"^\s*siesta:\s+Total\s*=\s*({FLOAT_RE})\s*$", text, re.IGNORECASE | re.MULTILINE)]
    fermi_values = [as_float(value) for value in re.findall(rf"^\s*siesta:\s+Fermi\s*=\s*({FLOAT_RE})\s*$", text, re.IGNORECASE | re.MULTILINE)]
    wall_values = [as_float(value) for value in re.findall(rf"^\s*timer:\s*Elapsed wall time \(sec\)\s*=\s*({FLOAT_RE})", text, re.IGNORECASE | re.MULTILINE)]
    max_force, force_rows = parse_force_block(text)
    fatal_patterns = {
        "SCF_NOT_CONV": r"\bSCF_NOT_CONV\b",
        "GEOM_NOT_CONV": r"\bGEOM_NOT_CONV\b",
        "STOPPING_PROGRAM": r"Stopping\s+Program",
        "FATAL_MARKER": r"^\s*(?:siesta:\s*)?FATAL\b",
        "ERROR_MARKER": r"^\s*(?:siesta:\s*)?ERROR\b",
    }
    fatal = [code for code, pattern in fatal_patterns.items() if re.search(pattern, text, re.IGNORECASE | re.MULTILINE)]
    warnings = len(re.findall(r"^\s*(?:siesta:\s*)?WARNING\b", text, re.IGNORECASE | re.MULTILINE))
    observables: dict[str, dict[str, Any]] = {}
    if total_values and total_values[-1] is not None:
        observables["total_energy"] = {"value": total_values[-1], "unit": "eV", "source": "final_energy_block"}
    if fermi_values and fermi_values[-1] is not None:
        observables["fermi_energy"] = {"value": fermi_values[-1], "unit": "eV", "source": "final_energy_block"}
    if max_force is not None:
        observables["max_force"] = {"value": max_force, "unit": "eV/Ang", "source": "final_atomic_forces_vector_norm"}
    if wall_values and wall_values[-1] is not None:
        observables["wall_time"] = {"value": wall_values[-1], "unit": "s", "source": "timer_elapsed_wall_time"}
    if scf_iterations:
        observables["final_scf_iterations"] = {"value": scf_iterations[-1], "unit": "iterations", "source": "final_scf_convergence_marker"}
    return {
        "versions": versions,
        "start_markers": starts,
        "end_markers": ends,
        "completion_markers": completions,
        "scf_cycle_count": len(scf_iterations),
        "scf_iterations": scf_iterations,
        "fatal_markers": fatal,
        "warning_count": warnings,
        "relaxed_coordinates": bool(re.search(r"outcoor:\s*Relaxed atomic coordinates", text, re.IGNORECASE)),
        "unrelaxed_coordinates": bool(re.search(r"outcoor:\s*Final \(unrelaxed\)", text, re.IGNORECASE)),
        "force_rows": force_rows,
        "observables": observables,
    }


def validate_parent_manifest(
    parent: dict[str, Any] | None,
    profile: dict[str, Any],
    restart_requested: bool,
    expected_version: str,
    plan: dict[str, Any],
    findings: list[dict[str, str]],
) -> None:
    needs_parent = bool(profile.get("requires_parent")) or restart_requested
    if not needs_parent:
        return

    def add(code: str, message: str) -> None:
        findings.append({"gate": "parent_ancestry", "severity": "error", "code": code, "message": message})

    if parent is None:
        add("PARENT_MANIFEST_MISSING", "This task or restart request requires a parent run manifest.")
        return
    required = {"schema_version", "record_id", "code", "code_version", "task_type", "case_id", "scientific_protocol_id", "status", "scientific_acceptance", "configuration", "metrics", "evidence", "limitations", "provenance"}
    if set(parent) != required or parent.get("schema_version") != "1.0":
        add("PARENT_MANIFEST_SCHEMA_INVALID", "The parent does not match the shared run-manifest schema 1.0 surface.")
    if not isinstance(parent.get("record_id"), str) or not ID_RE.fullmatch(parent["record_id"]):
        add("PARENT_RECORD_ID_INVALID", "Parent record_id is not a safe manifest identifier.")
    if parent.get("code") != "siesta" or normalize_version(str(parent.get("code_version", ""))) != normalize_version(expected_version):
        add("PARENT_CODE_VERSION_MISMATCH", "Parent code/version differs from the planned SIESTA executable.")
    if parent.get("case_id") != plan.get("case_id") or parent.get("scientific_protocol_id") != plan.get("scientific_protocol_id"):
        add("PARENT_PLAN_IDENTITY_MISMATCH", "Parent case or scientific protocol differs from the plan.")
    allowed_tasks = set(profile.get("allowed_parent_tasks", []))
    if allowed_tasks and parent.get("task_type") not in allowed_tasks:
        add("PARENT_TASK_INVALID", "Parent task type is incompatible with this task profile.")
    parent_status = parent.get("status")
    parent_acceptance = parent.get("scientific_acceptance")
    if (
        parent_status not in {"planned", "running", "completed", "stopped", "failed"}
        or parent_acceptance not in {"not_assessed", "requires_human_review"}
        or (parent_status != "completed" and parent_acceptance != "not_assessed")
    ):
        add("PARENT_STATE_INVALID", "Parent terminal and scientific-acceptance states are invalid.")
    if not isinstance(parent.get("configuration"), dict) or not isinstance(parent.get("metrics"), dict):
        add("PARENT_STRUCTURE_INVALID", "Parent configuration and metrics must be JSON objects.")
    if not isinstance(parent.get("limitations"), list) or any(not isinstance(item, str) for item in parent.get("limitations", [])):
        add("PARENT_LIMITATIONS_INVALID", "Parent limitations must be a string array.")
    provenance = parent.get("provenance")
    if (
        not isinstance(provenance, dict)
        or set(provenance) != {"collector", "collector_version", "generated_utc"}
        or any(not resolved_string(provenance.get(field)) for field in ("collector", "collector_version", "generated_utc"))
    ):
        add("PARENT_PROVENANCE_INVALID", "Parent provenance is incomplete or unresolved.")
    if profile.get("requires_parent"):
        if parent_status != "completed":
            add(
                "PARENT_SCIENTIFIC_RUN_NOT_COMPLETED",
                "A downstream scientific task requires a technically completed parent run.",
            )
        add(
            "PARENT_SCIENTIFIC_DECISION_BUNDLE_REQUIRED",
            "Downstream scientific ancestry requires an externally trusted bundle containing the calculation record, human scientific decision, and post-decision claim map; this CLI has no platform human-trust resolver.",
        )
    if restart_requested and parent_status != "completed":
        add("RESTART_PARENT_NOT_COMPLETED", "A restart requires a technically completed parent run.")
    evidence = parent.get("evidence")
    if not isinstance(evidence, list) or any(
        not isinstance(item, dict)
        or set(item) - {"role", "label", "status", "sha256"}
        or not resolved_string(item.get("role"))
        or not resolved_string(item.get("label"))
        or item.get("status") not in {"present", "missing", "redacted", "external"}
        or (item.get("status") == "present" and not SHA256_RE.fullmatch(str(item.get("sha256", ""))))
        or (item.get("status") == "missing" and item.get("sha256") is not None)
        for item in (evidence if isinstance(evidence, list) else [])
    ):
        add("PARENT_EVIDENCE_INVALID", "Parent evidence records are invalid or present records lack hashes.")
        return
    present_roles = {item["role"] for item in evidence if item.get("status") == "present" and SHA256_RE.fullmatch(str(item.get("sha256", "")))}
    required_roles = set(profile.get("required_parent_roles", []))
    if required_roles and not present_roles.intersection(required_roles):
        add("PARENT_REQUIRED_ROLE_MISSING", "Parent lacks a hashed evidence role accepted by the task profile.")
    if restart_requested and not present_roles.intersection({"density_matrix", "restart_checkpoint", "structure_checkpoint", "velocity_checkpoint", "siesta_nc"}):
        add("RESTART_EVIDENCE_MISSING", "Requested restart lacks hashed checkpoint evidence.")


def convergence_parameters(scalars: dict[str, list[str]], blocks: dict[str, list[list[str]]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    specs = {
        "mesh_cutoff": ("meshcutoff", True),
        "pao_energy_shift": ("paoenergyshift", True),
        "scf_dm_tolerance": ("scfdmtolerance", False),
        "scf_h_tolerance": ("scfhtolerance", True),
        "electronic_temperature": ("electronictemperature", True),
        "md_max_force_tolerance": ("mdmaxforcetol", True),
    }
    for name, (label, needs_unit) in specs.items():
        parsed = quantity(scalars.get(label), require_unit=needs_unit)
        if parsed is not None:
            result[name] = {"value": parsed[0], "unit": parsed[1], "source": "direct_fdf_input"}
    grid = blocks.get("kgridmonkhorstpack")
    if grid and len(grid) == 3 and all(len(row) == 4 for row in grid):
        try:
            matrix = [[int(value) for value in row[:3]] for row in grid]
            result["kpoint_count"] = {"value": abs(matrix_determinant(matrix)), "unit": "points", "source": "kgrid_monkhorst_pack_determinant"}
        except ValueError:
            pass
    cutoff = quantity(scalars.get("kgridcutoff"), require_unit=True)
    if cutoff is not None:
        result["kgrid_cutoff"] = {"value": cutoff[0], "unit": cutoff[1], "source": "direct_fdf_input"}
    return result


def audit(
    input_path: Path,
    mode: str,
    task_type: str,
    periodicity: str,
    output_path: Path | None,
    plan_path: Path,
    expected_version: str,
    pseudopotential_manifest_path: Path | None = None,
    parent_manifest_path: Path | None = None,
) -> tuple[dict[str, Any], int]:
    findings: list[dict[str, str]] = []

    def add(gate: str, code: str, message: str) -> None:
        findings.append({"gate": gate, "severity": "error", "code": code, "message": message})

    evidence: dict[str, Any] = {}
    if not input_path.is_file():
        add("fdf_syntax", "INPUT_MISSING", "The direct FDF input is unavailable.")
        return _report(mode, task_type, periodicity, expected_version, None, evidence, findings, {}, [], None), 2
    if not plan_path.is_file():
        add("scientific_plan", "PLAN_MISSING", "A scientific plan produced by create_siesta_plan.py is required.")
        return _report(mode, task_type, periodicity, expected_version, None, evidence, findings, {}, [], None), 2

    try:
        index, supplements, profiles = load_reference_contracts()
        plan = load_object(plan_path, "scientific plan")
        input_text = input_path.read_text(encoding="utf-8", errors="strict")
        scalars, blocks, labels, parser_findings = parse_fdf_text(input_text)
    except (OSError, UnicodeError, ValueError) as exc:
        add("official_source_resolution", "AUDIT_PREREQUISITE_UNREADABLE", type(exc).__name__)
        return _report(mode, task_type, periodicity, expected_version, None, evidence, findings, {}, [], None), 2

    input_info = digest(input_path)
    plan_info = digest(plan_path)
    evidence.update({"input": input_info, "plan": plan_info})
    findings.extend(parser_findings)
    findings.extend(validate_plan(plan, expected_task=task_type, expected_periodicity=periodicity, expected_version=expected_version))
    if index.get("code_version") != normalize_version(expected_version) or plan.get("documentation_line") != index.get("documentation_line"):
        add("official_source_resolution", "PINNED_VERSION_MISMATCH", "The plan/executable version is not covered by the pinned parameter index.")
    evidence["official_parameter_index"] = {**digest(OFFICIAL_INDEX), "source_commit": index["source_commit"], "code_version": index["code_version"]}
    findings.extend(validate_label_surface(labels, task_type, index, supplements, profiles))
    profile = profiles["profiles"][task_type]
    if not str(profile.get("input_maturity", "")).startswith("automated"):
        add("task_specific_validity", "TASK_INPUT_NOT_AUTOMATED", f"The {task_type} profile is documented but its input semantics are not automated.")

    present = set(scalars) | set(blocks)
    for required in profile.get("required_input_all", []):
        if canonical(required) not in present:
            add("numerical_controls", "TASK_REQUIRED_INPUT_MISSING", f"The {task_type} profile requires explicit {required}.")
    for group in profile.get("required_input_any", []):
        if not any(canonical(item) in present for item in group):
            add("numerical_controls", "TASK_REQUIRED_INPUT_ALTERNATIVE_MISSING", f"The {task_type} profile requires one of: {', '.join(group)}.")

    number_atoms = as_int(scalars.get("numberofatoms"))
    number_species = as_int(scalars.get("numberofspecies"))
    if number_atoms is None or number_atoms <= 0:
        add("structure_consistency", "NUMBER_OF_ATOMS_INVALID", "NumberOfAtoms must be one positive integer.")
    if number_species is None or number_species <= 0:
        add("structure_consistency", "NUMBER_OF_SPECIES_INVALID", "NumberOfSpecies must be one positive integer.")

    species_rows = blocks.get("chemicalspecieslabel")
    species: dict[int, tuple[int, str]] = {}
    if species_rows is None:
        add("structure_consistency", "SPECIES_BLOCK_MISSING", "ChemicalSpeciesLabel is required.")
    else:
        for row in species_rows:
            if len(row) not in (3, 4):
                add("structure_consistency", "SPECIES_ROW_INVALID", "Each ChemicalSpeciesLabel row must have three or four fields.")
                continue
            try:
                species_id, atomic_number = int(row[0]), int(row[1])
            except ValueError:
                add("structure_consistency", "SPECIES_ROW_NONINTEGER", "Species id and atomic number must be integers.")
                continue
            if species_id <= 0 or species_id in species or atomic_number == 0 or abs(atomic_number) > 200:
                add("structure_consistency", "SPECIES_ID_INVALID", "Species ids must be unique and positive; atomic numbers must be supported nonzero integers.")
                continue
            species[species_id] = (atomic_number, row[3] if len(row) == 4 else row[2])
        if number_species is not None and len(species_rows) != number_species:
            add("structure_consistency", "SPECIES_COUNT_MISMATCH", "NumberOfSpecies differs from ChemicalSpeciesLabel rows.")

    coordinate_rows = blocks.get("atomiccoordinatesandatomicspecies")
    if "atomiccoordinatesformat" not in scalars:
        add("structure_consistency", "COORDINATE_FORMAT_MISSING", "AtomicCoordinatesFormat must be explicit.")
    if coordinate_rows is None:
        add("structure_consistency", "COORDINATES_BLOCK_MISSING", "AtomicCoordinatesAndAtomicSpecies is required.")
    else:
        if number_atoms is not None and len(coordinate_rows) != number_atoms:
            add("structure_consistency", "ATOM_COUNT_MISMATCH", "NumberOfAtoms differs from coordinate rows.")
        for row in coordinate_rows:
            if len(row) < 4:
                add("structure_consistency", "COORDINATE_ROW_INVALID", "Each coordinate row needs three coordinates and one species id.")
                continue
            try:
                values = [float(value) for value in row[:3]]
                row_species = int(row[3])
            except ValueError:
                add("structure_consistency", "COORDINATE_ROW_NONNUMERIC", "Coordinates and species ids must be numeric.")
                continue
            if not all(math.isfinite(value) for value in values):
                add("structure_consistency", "COORDINATE_NONFINITE", "Coordinates must be finite.")
            if row_species not in species:
                add("structure_consistency", "COORDINATE_SPECIES_UNKNOWN", "A coordinate references an undefined species id.")

    if quantity(scalars.get("latticeconstant"), require_unit=True) is None:
        add("structure_consistency", "LATTICE_CONSTANT_INVALID", "LatticeConstant must be explicit, positive, and include a unit.")
    lattice_rows = blocks.get("latticevectors") or blocks.get("latticeparameters")
    if lattice_rows is None:
        add("structure_consistency", "LATTICE_DEFINITION_MISSING", "LatticeVectors or LatticeParameters is required by this profile.")
    elif "latticevectors" in blocks:
        if len(lattice_rows) != 3 or any(len(row) != 3 for row in lattice_rows):
            add("structure_consistency", "LATTICE_VECTORS_INVALID", "LatticeVectors must contain three rows of three values.")
        elif any(as_float(value) is None for row in lattice_rows for value in row):
            add("structure_consistency", "LATTICE_VECTORS_NONNUMERIC", "LatticeVectors must be finite numbers.")

    required_scalars = ("xcfunctional", "xcauthors", "meshcutoff", "maxscfiterations", "scfmustconverge", "spin", "solutionmethod", "occupationfunction", "electronictemperature")
    for label in required_scalars:
        if label not in scalars:
            add("numerical_controls", "REPRODUCIBILITY_CONTROL_MISSING", f"{label} must be explicit in this profile.")
    for label in ("meshcutoff", "paoenergyshift", "scfhtolerance", "electronictemperature"):
        if label in scalars and quantity(scalars[label], require_unit=True) is None:
            add("numerical_controls", "QUANTITY_INVALID", f"{label} must be a positive quantity with a unit.")
    if "scfdmtolerance" in scalars and quantity(scalars["scfdmtolerance"], require_unit=False) is None:
        add("numerical_controls", "SCF_DM_TOLERANCE_INVALID", "SCF.DM.Tolerance must be a positive dimensionless value.")
    if truth_value(scalars.get("scfmustconverge")) is not True:
        add("numerical_controls", "SCF_MUST_CONVERGE_NOT_TRUE", "SCF.MustConverge must be explicitly true.")
    if (as_int(scalars.get("maxscfiterations")) or 0) <= 0:
        add("numerical_controls", "SCF_ITERATION_LIMIT_INVALID", "MaxSCFIterations must be positive.")
    if "paobasis" not in blocks and not ({"paobasissize", "paoenergyshift"} <= set(scalars)):
        add("numerical_controls", "BASIS_DEFINITION_INCOMPLETE", "Provide PAO.Basis or both PAO.BasisSize and PAO.EnergyShift.")

    kgrid_block = blocks.get("kgridmonkhorstpack")
    kgrid_cutoff = scalars.get("kgridcutoff")
    if periodicity != "molecule":
        if kgrid_block is not None and kgrid_cutoff is not None:
            add("numerical_controls", "KGRID_MULTIPLE_CONTROLS", "Use one explicit periodic k-grid control in the audited core.")
        elif kgrid_block is None and kgrid_cutoff is None:
            add("numerical_controls", "KGRID_MISSING", "A wire/slab/bulk case needs kgrid.MonkhorstPack or kgrid.Cutoff.")
        elif kgrid_cutoff is not None and quantity(kgrid_cutoff, require_unit=True) is None:
            add("numerical_controls", "KGRID_CUTOFF_INVALID", "kgrid.Cutoff must be positive and include a unit.")
        elif kgrid_block is not None:
            if len(kgrid_block) != 3 or any(len(row) != 4 for row in kgrid_block):
                add("numerical_controls", "KGRID_BLOCK_INVALID", "kgrid.MonkhorstPack must contain three rows of three integers plus one shift.")
            else:
                try:
                    matrix = [[int(value) for value in row[:3]] for row in kgrid_block]
                    shifts = [float(row[3]) for row in kgrid_block]
                    if matrix_determinant(matrix) == 0 or not all(math.isfinite(value) for value in shifts):
                        raise ValueError
                except ValueError:
                    add("numerical_controls", "KGRID_VALUES_INVALID", "The k-grid matrix must be nonsingular and shifts finite.")

    if task_type == "relax":
        if truth_value(scalars.get("geometrymustconverge")) is not True:
            add("numerical_controls", "GEOMETRY_MUST_CONVERGE_NOT_TRUE", "GeometryMustConverge must be explicitly true.")
        if quantity(scalars.get("mdmaxforcetol"), require_unit=True) is None:
            add("numerical_controls", "RELAX_FORCE_TOLERANCE_INVALID", "MD.MaxForceTol must be positive and include a unit.")
        if (as_int(scalars.get("mdsteps")) or 0) <= 0:
            add("numerical_controls", "RELAX_STEP_LIMIT_INVALID", "MD.Steps must be a positive integer.")
        variable_cell = truth_value(scalars.get("mdvariablecell"))
        if variable_cell is None:
            add("numerical_controls", "RELAX_VARIABLE_CELL_UNRESOLVED", "MD.VariableCell must be explicit for the automated relaxation core.")
        elif variable_cell:
            add("task_specific_validity", "VARIABLE_CELL_RELAX_NOT_AUTOMATED", "Stress/variable-cell validity is documented but not automated.")

    pseudo_records: list[dict[str, Any]] = []
    for species_id, (atomic_number, spec) in sorted(species.items()):
        spec_path = Path(spec)
        if spec_path.is_absolute():
            add("pseudopotential_provenance", "PSEUDO_ABSOLUTE_PATH", "Absolute pseudopotential paths are not portable in this profile.")
            base = spec_path
        else:
            base = input_path.parent / spec_path
        suffix = spec_path.suffix.casefold()
        if suffix:
            if suffix not in PSEUDO_SUFFIXES:
                add("pseudopotential_provenance", "PSEUDO_FORMAT_UNSUPPORTED", "The pseudopotential suffix is not .vps, .psf, or .psml.")
                continue
            candidates = [base]
        else:
            candidates = [Path(f"{base}{extension}") for extension in PSEUDO_SUFFIXES]
        existing = [candidate for candidate in candidates if candidate.is_file()]
        if not existing:
            add("pseudopotential_provenance", "PSEUDO_MISSING", "No local pseudopotential resolved for a declared species.")
            continue
        if len(existing) > 1:
            add("pseudopotential_provenance", "PSEUDO_PRECEDENCE_AMBIGUOUS", "Multiple implicit pseudopotential formats exist.")
            continue
        selected = existing[0]
        record = {"species_index": species_id, "atomic_number": atomic_number, "format": selected.suffix.casefold().lstrip("."), **digest(selected)}
        if selected.suffix.casefold() == ".psml":
            embedded_xc = psml_xc_identity(selected)
            if embedded_xc is None:
                add("pseudopotential_provenance", "PSEUDO_PSML_XC_UNREADABLE", "A PSML file is not readable XML, so its embedded XC identity cannot be verified.")
            elif embedded_xc["family"] is None:
                add("pseudopotential_provenance", "PSEUDO_PSML_XC_UNRESOLVED", "A PSML file does not expose a recognized embedded LibXC identity.")
            else:
                record["embedded_xc_family"] = embedded_xc["family"]
                record["embedded_xc_functional_ids"] = embedded_xc["functional_ids"]
        pseudo_records.append(record)

    manifest_path = pseudopotential_manifest_path or input_path.with_name("pseudopotential-manifest.json")
    manifest_info: dict[str, Any] | None = None
    manifest: dict[str, Any] | None = None
    if not manifest_path.is_file():
        add("pseudopotential_provenance", "PSEUDO_MANIFEST_MISSING", "Pseudopotential manifest schema 2.0 is required.")
    else:
        manifest_info = digest(manifest_path)
        evidence["pseudopotential_manifest"] = manifest_info
        try:
            manifest = load_object(manifest_path, "pseudopotential manifest")
        except ValueError:
            add("pseudopotential_provenance", "PSEUDO_MANIFEST_INVALID", "The pseudopotential manifest is unreadable.")
    if manifest is not None:
        records = manifest.get("pseudopotentials")
        if set(manifest) != {"schema_version", "pseudopotentials"} or manifest.get("schema_version") != "2.0" or not isinstance(records, list):
            add("pseudopotential_provenance", "PSEUDO_MANIFEST_SCHEMA_INVALID", "The pseudopotential manifest does not match schema 2.0.")
            records = []
        declared: dict[int, dict[str, Any]] = {}
        keys = {"species_index", "format", "expected_sha256", "source", "xc_family", "relativistic_treatment", "valence_configuration", "source_version", "validation_id"}
        for record in records:
            if not isinstance(record, dict) or set(record) != keys:
                add("pseudopotential_provenance", "PSEUDO_MANIFEST_RECORD_INVALID", "Each pseudopotential record must contain the exact schema 2.0 fields.")
                continue
            sid = record.get("species_index")
            if not isinstance(sid, int) or sid <= 0 or sid in declared:
                add("pseudopotential_provenance", "PSEUDO_MANIFEST_SPECIES_INVALID", "Manifest species ids must be unique positive integers.")
                continue
            if record.get("format") not in {"vps", "psf", "psml"} or not SHA256_RE.fullmatch(str(record.get("expected_sha256", ""))):
                add("pseudopotential_provenance", "PSEUDO_MANIFEST_IDENTITY_INVALID", "Manifest format or SHA-256 is invalid.")
                continue
            if any(not resolved_string(record.get(field)) for field in ("source", "xc_family", "relativistic_treatment", "valence_configuration", "source_version", "validation_id")):
                add("pseudopotential_provenance", "PSEUDO_MANIFEST_METADATA_UNRESOLVED", "XC, relativity, valence, source version, validation, and source identity must be resolved and privacy-safe.")
                continue
            if record["relativistic_treatment"].casefold() not in {"nonrelativistic", "scalar-relativistic", "fully-relativistic"}:
                add("pseudopotential_provenance", "PSEUDO_RELATIVITY_INVALID", "Relativistic treatment must use the controlled vocabulary.")
                continue
            declared[sid] = record
        if set(declared) != set(species):
            add("pseudopotential_provenance", "PSEUDO_MANIFEST_COVERAGE_MISMATCH", "Manifest species coverage differs from ChemicalSpeciesLabel.")
        actual = {record["species_index"]: record for record in pseudo_records}
        input_xc = canonical(" ".join(scalars.get("xcfunctional", []) + scalars.get("xcauthors", [])))
        requires_soc = bool({"soc", "spin-orbit", "spinorbit"}.intersection(set(plan.get("declared_features", []))))
        for sid, record in actual.items():
            expected = declared.get(sid)
            if expected is None:
                continue
            if expected["expected_sha256"] != record["sha256"] or expected["format"] != record["format"]:
                add("pseudopotential_provenance", "PSEUDO_MANIFEST_IDENTITY_MISMATCH", "A local pseudopotential differs from its declared format/hash.")
                continue
            embedded_family = record.get("embedded_xc_family")
            if embedded_family and xc_family_class(expected["xc_family"]) != xc_family_class(embedded_family):
                add("pseudopotential_provenance", "PSEUDO_PSML_XC_MISMATCH", "The manifest XC family differs from the XC identity embedded in the PSML file.")
            if input_xc and not all(token in canonical(expected["xc_family"]) for token in filter(None, (canonical(" ".join(scalars.get("xcfunctional", []))), canonical(" ".join(scalars.get("xcauthors", [])))))):
                add("pseudopotential_provenance", "PSEUDO_XC_MISMATCH", "Pseudopotential XC family differs from explicit XC.Functional/XC.Authors.")
            if requires_soc and expected["relativistic_treatment"].casefold() != "fully-relativistic":
                add("pseudopotential_provenance", "PSEUDO_SOC_INCOMPATIBLE", "A declared SOC workflow requires fully-relativistic pseudopotentials.")
            record.update({
                "source_identity_sha256": hashlib.sha256(expected["source"].encode()).hexdigest(),
                "source_version_sha256": hashlib.sha256(expected["source_version"].encode()).hexdigest(),
                "validation_id_sha256": hashlib.sha256(expected["validation_id"].encode()).hexdigest(),
                "xc_family": expected["xc_family"],
                "relativistic_treatment": expected["relativistic_treatment"],
                "source_status": "declared_and_hash_bound",
            })

    restart_requested = any(truth_value(scalars.get(label)) is True for label in ("dmusesavedm", "usesavedata", "mdusesavecg", "mdusesavexv"))
    parent: dict[str, Any] | None = None
    if parent_manifest_path is not None:
        if parent_manifest_path.is_file():
            evidence["parent_manifest"] = digest(parent_manifest_path)
            try:
                parent = load_object(parent_manifest_path, "parent manifest")
            except ValueError:
                add("parent_ancestry", "PARENT_MANIFEST_INVALID", "The parent manifest is unreadable.")
        else:
            add("parent_ancestry", "PARENT_MANIFEST_MISSING", "The supplied parent manifest is unavailable.")
    validate_parent_manifest(parent, profile, restart_requested, expected_version, plan, findings)

    parameters = convergence_parameters(scalars, blocks)
    evidence["convergence_parameters"] = parameters
    output_summary: dict[str, Any] | None = None
    if mode == "run":
        if output_path is None or not output_path.is_file():
            add("execution_completion", "OUTPUT_MISSING", "Run mode requires a readable standard-output file.")
        else:
            evidence["output"] = digest(output_path)
            output_text = output_path.read_text(encoding="utf-8", errors="replace")
            output_summary = parse_output_text(output_text)
            evidence["observables"] = output_summary["observables"]
            echoed = extract_echo(output_text)
            expected_echo = normalized_fdf_lines(input_text)
            echo_pass = echoed == expected_echo
            evidence["input_echo"] = {
                "status": "exact_normalized_match" if echo_pass else "mismatch_or_unresolved",
                "input_line_count": len(expected_echo),
                "echo_line_count": len(echoed) if echoed is not None else None,
            }
            if not echo_pass:
                add("input_output_consistency", "INPUT_ECHO_MISMATCH", "The unique output input-dump does not exactly match the normalized direct FDF input.")
            if len(output_summary["versions"]) != 1 or output_summary["start_markers"] != 1 or output_summary["end_markers"] != 1 or output_summary["completion_markers"] != 1:
                add("execution_completion", "RUN_BOUNDARY_MARKERS_INVALID", "Exactly one version, start, end, and Job completed marker is required; concatenated or partial output is blocked.")
            observed_version = output_summary["versions"][0] if len(output_summary["versions"]) == 1 else None
            if observed_version is None or normalize_version(observed_version) != normalize_version(expected_version):
                add("official_version_match", "OUTPUT_VERSION_MISMATCH", "Observed SIESTA version differs from the plan and --expected-version.")
            for marker in output_summary["fatal_markers"]:
                gate = "electronic_convergence" if marker == "SCF_NOT_CONV" else ("task_specific_validity" if marker == "GEOM_NOT_CONV" else "execution_completion")
                add(gate, marker, f"Blocking output marker {marker} was found.")
            if output_summary["warning_count"]:
                add("output_warnings", "WARNING_MARKER", "Unresolved SIESTA WARNING markers were found.")
            if not output_summary["scf_iterations"]:
                add("electronic_convergence", "SCF_CONVERGENCE_MISSING", "No SCF cycle converged marker was found.")
            for observable in profile.get("required_output_observables", []):
                if observable not in output_summary["observables"]:
                    add("output_observables", "REQUIRED_OBSERVABLE_MISSING", f"The {task_type} profile requires extracted {observable} evidence.")
            if task_type == "relax" and not any(item["gate"] == "task_specific_validity" for item in findings):
                if not output_summary["relaxed_coordinates"] or output_summary["unrelaxed_coordinates"]:
                    add("task_specific_validity", "RELAXED_GEOMETRY_NOT_DEMONSTRATED", "Fixed-cell relaxation lacks an unambiguous relaxed-coordinate marker.")
                tolerance = parameters.get("md_max_force_tolerance")
                observed = output_summary["observables"].get("max_force")
                if isinstance(tolerance, dict) and isinstance(observed, dict):
                    compatible_units = canonical(str(tolerance.get("unit"))) in {"evang", "evangstrom"}
                    if not compatible_units:
                        add("task_specific_validity", "RELAX_FORCE_UNIT_UNSUPPORTED", "Automated force comparison currently requires eV/Ang.")
                    elif float(observed["value"]) > float(tolerance["value"]):
                        add("task_specific_validity", "RELAX_FORCE_TOLERANCE_FAILED", "Final maximum atomic-force norm exceeds MD.MaxForceTol.")

    evidence.setdefault("observables", {})
    result = _report(mode, task_type, periodicity, expected_version, plan, evidence, findings, {
        "number_of_atoms": number_atoms,
        "number_of_species": number_species,
        "coordinate_format": " ".join(scalars.get("atomiccoordinatesformat", [])) or None,
        "xc_functional": " ".join(scalars.get("xcfunctional", [])) or None,
        "xc_authors": " ".join(scalars.get("xcauthors", [])) or None,
        "basis_size": " ".join(scalars.get("paobasissize", [])) or ("explicit-block" if "paobasis" in blocks else None),
        "mesh_cutoff": " ".join(scalars.get("meshcutoff", [])) or None,
        "spin": " ".join(scalars.get("spin", [])) or None,
        "restart_requested": restart_requested,
    }, pseudo_records, output_summary)
    return result, 0 if result["decision"] == "pass" else 2


def _report(
    mode: str,
    task_type: str,
    periodicity: str,
    expected_version: str,
    plan: dict[str, Any] | None,
    evidence: dict[str, Any],
    findings: list[dict[str, str]],
    selected_inputs: dict[str, Any],
    pseudopotentials: list[dict[str, Any]],
    output_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    gate_names = (
        "scientific_plan", "official_source_resolution", "fdf_syntax", "fdf_semantics", "structure_consistency",
        "pseudopotential_provenance", "numerical_controls", "parent_ancestry", "official_version_match",
        "input_output_consistency", "execution_completion", "electronic_convergence", "output_warnings",
        "output_observables", "numerical_convergence", "task_specific_validity", "physical_validity", "scientific_acceptance",
    )
    blocked = {item["gate"] for item in findings if item.get("severity") == "error"}
    gates: dict[str, str] = {}
    for gate in gate_names:
        if gate in blocked:
            gates[gate] = "blocked"
        elif gate in {"numerical_convergence", "physical_validity"}:
            gates[gate] = "not_assessed"
        elif gate == "scientific_acceptance":
            gates[gate] = "blocked"
        elif gate == "task_specific_validity":
            gates[gate] = "pass" if mode == "run" and task_type == "relax" else "not_assessed"
        elif gate in {"official_version_match", "input_output_consistency", "execution_completion", "electronic_convergence", "output_warnings", "output_observables"} and mode == "input":
            gates[gate] = "not_applicable"
        else:
            gates[gate] = "pass"
    required = ["scientific_plan", "official_source_resolution", "fdf_syntax", "fdf_semantics", "structure_consistency", "pseudopotential_provenance", "numerical_controls", "parent_ancestry"]
    if mode == "run":
        required += ["official_version_match", "input_output_consistency", "execution_completion", "electronic_convergence", "output_warnings", "output_observables"]
        if task_type == "relax":
            required.append("task_specific_validity")
    decision = "pass" if not blocked and all(gates[name] == "pass" for name in required) else "block"
    case_id = plan.get("case_id") if isinstance(plan, dict) and isinstance(plan.get("case_id"), str) else None
    observed_version = output_summary["versions"][0] if output_summary and len(output_summary["versions"]) == 1 else None
    return {
        "schema_version": SCHEMA_VERSION,
        "auditor": "audit_siesta_case.py",
        "auditor_version": TOOL_VERSION,
        "code": "siesta",
        "mode": mode,
        "task_type": task_type,
        "periodicity": periodicity,
        "case_id": case_id,
        "scientific_protocol_id": plan.get("scientific_protocol_id") if isinstance(plan, dict) else None,
        "state_id": plan.get("state_id") if isinstance(plan, dict) else None,
        "expected_code_version": normalize_version(expected_version),
        "observed_code_version": observed_version,
        "decision": decision,
        "maximum_conclusion": "technical_run_gates_passed_scientific_claim_blocked" if decision == "pass" and mode == "run" else ("technical_input_gates_passed_scientific_claim_blocked" if decision == "pass" else "blocked_by_deterministic_findings"),
        "selected_inputs": selected_inputs,
        "pseudopotentials": pseudopotentials,
        "output_summary": output_summary,
        "evidence": evidence,
        "findings": findings,
        "gates": gates,
        "limitations": [
            "Only direct FDF and the task-profile surface are automated; includes and official labels outside that surface remain blocked.",
            "The pinned parameter index establishes documented/source behavior, not scientific sufficiency or optimal settings.",
            "A passing audit does not prove numerical convergence, basis completeness, physical validity, or scientific acceptance.",
        ],
        "provenance": {"collector": "audit_siesta_case.py", "collector_version": TOOL_VERSION, "generated_utc": generated_utc()},
    }


def atomic_write(path: Path, rendered: str) -> None:
    if path.exists():
        raise ValueError("refusing to overwrite an existing report")
    if not path.parent.is_dir():
        raise ValueError("report output parent directory does not exist")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        handle.write(rendered)
        staged = Path(handle.name)
    os.replace(staged, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--mode", choices=("input", "run"), default="input")
    parser.add_argument("--task-type", choices=ALL_TASKS, required=True)
    parser.add_argument("--periodicity", choices=PERIODICITIES, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pseudopotential-manifest", type=Path)
    parser.add_argument("--parent-manifest", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    if args.mode == "input" and args.output is not None:
        parser.error("--output is only valid with --mode run")
    result, status = audit(args.input, args.mode, args.task_type, args.periodicity, args.output, args.plan, args.expected_version, args.pseudopotential_manifest, args.parent_manifest)
    rendered = json.dumps(result, indent=2 if args.pretty else None, sort_keys=True) + "\n"
    try:
        atomic_write(args.out, rendered) if args.out else sys.stdout.write(rendered)
    except (OSError, ValueError) as exc:
        print(json.dumps({"decision": "block", "error_type": type(exc).__name__, "message": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    return status


if __name__ == "__main__":
    raise SystemExit(main())
