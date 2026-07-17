from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .utils import sha256_file, utc_now


RY_TO_EV = 13.605693122994
FLOAT = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?"


def _warning_lines(lines: list[str], limit: int = 50) -> list[str]:
    return [line.strip()[:500] for line in lines if re.search(r"\bwarning\b", line, re.IGNORECASE)][:limit]


def parse_qe_text(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    version_match = re.search(r"Program\s+([A-Za-z0-9_.+-]+)\s+v\.?([^\s]+)", text, re.IGNORECASE)
    energy_ry = [float(value) for value in re.findall(rf"!\s+total energy\s*=\s*({FLOAT})\s+Ry", text, re.IGNORECASE)]
    force_ry_bohr = [float(value) for value in re.findall(rf"Total force\s*=\s*({FLOAT})", text, re.IGNORECASE)]
    completed = "JOB DONE." in text
    electronic_converged = "convergence has been achieved" in text.lower()
    iterations = len(re.findall(r"^\s*iteration\s+#", text, re.MULTILINE | re.IGNORECASE))
    return {
        "schema_version": "1.0",
        "code": "qe",
        "program": version_match.group(1) if version_match else None,
        "code_version": version_match.group(2) if version_match else None,
        "completed": completed,
        "electronic_converged": electronic_converged,
        "ionic_converged": "bfgs converged" in text.lower() or "end of bfgs geometry optimization" in text.lower(),
        "scf_iterations_observed": iterations,
        "energy_trace_ev": [value * RY_TO_EV for value in energy_ry],
        "final_energy_ev": energy_ry[-1] * RY_TO_EV if energy_ry else None,
        "total_force_trace_ry_bohr": force_ry_bohr,
        "warnings": _warning_lines(lines),
        "limitations": [] if version_match else ["QE executable version was not parsed"],
    }


def parse_vasp_text(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    version_match = re.search(r"\bvasp\.([^\s]+)", text, re.IGNORECASE)
    energies = [float(value) for value in re.findall(rf"free\s+energy\s+TOTEN\s*=\s*({FLOAT})\s+eV", text, re.IGNORECASE)]
    completed = "General timing and accounting informations for this job" in text
    electronic_steps = len(re.findall(r"^\s*(?:DAV|RMM):", text, re.MULTILINE))
    return {
        "schema_version": "1.0",
        "code": "vasp",
        "program": "vasp",
        "code_version": version_match.group(1) if version_match else None,
        "completed": completed,
        "electronic_converged": "aborting loop because EDIFF is reached" in text,
        "ionic_converged": "reached required accuracy" in text,
        "scf_iterations_observed": electronic_steps,
        "energy_trace_ev": energies,
        "final_energy_ev": energies[-1] if energies else None,
        "warnings": _warning_lines(lines),
        "limitations": [] if version_match else ["VASP version was not parsed"],
    }


def detect_code(text: str) -> str:
    if re.search(r"\bProgram\s+(?:PWSCF|PHONON|NEB)\b", text, re.IGNORECASE) or "JOB DONE." in text:
        return "qe"
    if re.search(r"\bvasp\.", text, re.IGNORECASE) or "free  energy   TOTEN" in text:
        return "vasp"
    raise ValueError("could not detect QE or VASP output")


def extract_summary(path: Path, code: str = "auto") -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    selected = detect_code(text) if code == "auto" else code
    result = parse_qe_text(text) if selected == "qe" else parse_vasp_text(text)
    result["source"] = {"label": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)}
    result["generated_utc"] = utc_now()
    if not result["completed"]:
        result["limitations"].append("completion marker was not found")
    return result
