#!/usr/bin/env python3
"""Create and validate the scientific objective contract for a SIESTA workflow."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any


SCHEMA_VERSION = "2.0"
TOOL_VERSION = "2.0.0"
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
VERSION_RE = re.compile(r"^\d+(?:\.\d+){1,2}(?:[-+._A-Za-z0-9]*)?$")
PERIODICITIES = ("molecule", "wire", "slab", "bulk")
WORKFLOW_STAGES = ("exploratory", "convergence", "production", "postprocess")
TASK_WORKFLOWS = {
    "scf": ["ground-state-scf"],
    "relax": ["geometry-relaxation", "production-static-on-final-geometry"],
    "md": ["initial-state-validation", "equilibration", "production-trajectory", "statistical-analysis"],
    "bands": ["accepted-ground-state-parent", "band-path-evaluation", "band-postprocessing"],
    "dos": ["accepted-ground-state-parent", "dos-sampling", "dos-postprocessing"],
    "phonon": ["accepted-structure-parent", "force-constant-generation", "phonon-postprocessing"],
    "transiesta": ["accepted-electrodes", "accepted-device-parent", "negf-scf", "transport-postprocessing"],
    "tbtrans": ["accepted-transiesta-parent", "transport-sampling", "transport-postprocessing"],
    "optics": ["accepted-ground-state-parent", "optical-response", "response-postprocessing"],
    "tddft": ["accepted-ground-state-parent", "real-time-propagation", "spectrum-postprocessing"],
    "generic": ["explicit-manual-workflow-profile"],
}


def generated_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_version(value: str) -> str:
    return value.strip().removeprefix("v")


def documentation_line(version: str) -> str:
    numeric = re.match(r"^(\d+)\.(\d+)", normalize_version(version))
    if numeric is None:
        raise ValueError("SIESTA version must start with major.minor")
    return f"{numeric.group(1)}.{numeric.group(2)}"


def finite_nonnegative(value: float | None) -> bool:
    return value is None or (not isinstance(value, bool) and math.isfinite(value) and value >= 0)


def build_plan(
    *,
    case_id: str,
    protocol_id: str,
    state_id: str,
    task_type: str,
    siesta_version: str,
    periodicity: str,
    workflow_stage: str,
    objective: str,
    observable: str,
    observable_unit: str,
    normalization: str,
    reference: str,
    absolute_tolerance: float | None,
    relative_tolerance: float | None,
    acceptance_criteria: list[str],
    features: list[str],
) -> dict[str, Any]:
    for label, value in (("case_id", case_id), ("protocol_id", protocol_id), ("state_id", state_id)):
        if not ID_RE.fullmatch(value):
            raise ValueError(f"{label} must be an anonymized safe identifier of 3-128 characters")
    version = normalize_version(siesta_version)
    if not VERSION_RE.fullmatch(version):
        raise ValueError("siesta_version must be an explicit dotted numeric version")
    if task_type not in TASK_WORKFLOWS:
        raise ValueError("unsupported task_type")
    if periodicity not in PERIODICITIES or workflow_stage not in WORKFLOW_STAGES:
        raise ValueError("unsupported periodicity or workflow_stage")
    strings = {
        "objective": objective,
        "observable": observable,
        "observable_unit": observable_unit,
        "normalization": normalization,
        "reference": reference,
    }
    if any(not isinstance(value, str) or not value.strip() for value in strings.values()):
        raise ValueError("objective and observable contract strings must be nonempty")
    if absolute_tolerance is None and relative_tolerance is None:
        raise ValueError("provide an absolute or relative tolerance")
    if not finite_nonnegative(absolute_tolerance) or not finite_nonnegative(relative_tolerance):
        raise ValueError("tolerances must be finite nonnegative numbers")
    criteria = [item.strip() for item in acceptance_criteria if item.strip()]
    if not criteria:
        raise ValueError("provide at least one explicit acceptance criterion")
    feature_values = sorted(set(item.strip().casefold() for item in features if item.strip()))
    if any(not ID_RE.fullmatch(item) for item in feature_values):
        raise ValueError("feature labels must be safe opaque identifiers")
    return {
        "schema_version": SCHEMA_VERSION,
        "producer": "create_siesta_plan.py",
        "producer_version": TOOL_VERSION,
        "code": "siesta",
        "case_id": case_id,
        "scientific_protocol_id": protocol_id,
        "state_id": state_id,
        "task_type": task_type,
        "siesta_version": version,
        "documentation_line": documentation_line(version),
        "periodicity": periodicity,
        "workflow_stage": workflow_stage,
        "objective": objective.strip(),
        "observable": {
            "name": observable.strip(),
            "unit": observable_unit.strip(),
            "normalization": normalization.strip(),
            "reference": reference.strip(),
            "absolute_tolerance": absolute_tolerance,
            "relative_tolerance": relative_tolerance,
        },
        "declared_features": feature_values,
        "acceptance_criteria": criteria,
        "minimum_workflow": TASK_WORKFLOWS[task_type],
        "decision": "pass",
        "state": "plan_ready",
        "limitations": [
            "The minimum workflow is a deterministic baseline, not a universal complete workflow.",
            "Material-, model-, state-, and observable-specific evidence may require additional stages and convergence dimensions.",
            "A valid plan does not make an input ready or a result scientifically accepted.",
        ],
        "provenance": {
            "collector": "create_siesta_plan.py",
            "collector_version": TOOL_VERSION,
            "generated_utc": generated_utc(),
        },
    }


def validate_plan(
    plan: Any,
    *,
    expected_task: str | None = None,
    expected_periodicity: str | None = None,
    expected_version: str | None = None,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def add(code: str, message: str) -> None:
        findings.append({"gate": "scientific_plan", "severity": "error", "code": code, "message": message})

    if not isinstance(plan, dict):
        add("PLAN_SCHEMA_INVALID", "The scientific plan is not a JSON object.")
        return findings
    required = {
        "schema_version",
        "producer",
        "producer_version",
        "code",
        "case_id",
        "scientific_protocol_id",
        "state_id",
        "task_type",
        "siesta_version",
        "documentation_line",
        "periodicity",
        "workflow_stage",
        "objective",
        "observable",
        "declared_features",
        "acceptance_criteria",
        "minimum_workflow",
        "decision",
        "state",
        "limitations",
        "provenance",
    }
    if set(plan) != required:
        add("PLAN_FIELDS_INVALID", "The scientific plan fields do not match schema 2.0.")
    if plan.get("schema_version") != SCHEMA_VERSION or plan.get("producer") != "create_siesta_plan.py" or plan.get("producer_version") != TOOL_VERSION:
        add("PLAN_PRODUCER_INVALID", "The plan was not produced by the current SIESTA plan tool.")
    if plan.get("code") != "siesta" or plan.get("decision") != "pass" or plan.get("state") != "plan_ready":
        add("PLAN_STATE_INVALID", "The plan code or decision state is invalid.")
    for field in ("case_id", "scientific_protocol_id", "state_id"):
        if not isinstance(plan.get(field), str) or not ID_RE.fullmatch(plan[field]):
            add("PLAN_IDENTIFIER_INVALID", f"Plan {field} is not a safe anonymous identifier.")
    task = plan.get("task_type")
    if task not in TASK_WORKFLOWS or plan.get("minimum_workflow") != TASK_WORKFLOWS.get(task):
        add("PLAN_TASK_INVALID", "The task type or deterministic minimum workflow is invalid.")
    if expected_task is not None and task != expected_task:
        add("PLAN_TASK_MISMATCH", "The requested audit task differs from the plan.")
    periodicity = plan.get("periodicity")
    if periodicity not in PERIODICITIES:
        add("PLAN_PERIODICITY_INVALID", "The planned periodicity is invalid.")
    if expected_periodicity is not None and periodicity != expected_periodicity:
        add("PLAN_PERIODICITY_MISMATCH", "The requested audit periodicity differs from the plan.")
    version = plan.get("siesta_version")
    if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
        add("PLAN_VERSION_INVALID", "The planned SIESTA version is invalid.")
    else:
        if plan.get("documentation_line") != documentation_line(version):
            add("PLAN_DOCUMENTATION_LINE_INVALID", "The documentation line does not match the planned SIESTA version.")
        if expected_version is not None and normalize_version(expected_version) != version:
            add("PLAN_VERSION_MISMATCH", "The audit expected version differs from the plan.")
    if plan.get("workflow_stage") not in WORKFLOW_STAGES or not isinstance(plan.get("objective"), str) or not plan["objective"].strip():
        add("PLAN_OBJECTIVE_INVALID", "The workflow stage or objective is invalid.")
    observable = plan.get("observable")
    observable_fields = {"name", "unit", "normalization", "reference", "absolute_tolerance", "relative_tolerance"}
    if not isinstance(observable, dict) or set(observable) != observable_fields:
        add("PLAN_OBSERVABLE_INVALID", "The observable contract does not match schema 2.0.")
    else:
        for field in ("name", "unit", "normalization", "reference"):
            if not isinstance(observable.get(field), str) or not observable[field].strip():
                add("PLAN_OBSERVABLE_INVALID", f"Observable {field} is unresolved.")
        absolute = observable.get("absolute_tolerance")
        relative = observable.get("relative_tolerance")
        if absolute is None and relative is None:
            add("PLAN_TOLERANCE_INVALID", "The plan has no numerical tolerance.")
        if not finite_nonnegative(absolute) or not finite_nonnegative(relative):
            add("PLAN_TOLERANCE_INVALID", "Plan tolerances must be finite nonnegative numbers.")
    if not isinstance(plan.get("declared_features"), list) or any(not isinstance(item, str) or not ID_RE.fullmatch(item) for item in plan.get("declared_features", [])):
        add("PLAN_FEATURES_INVALID", "Declared feature labels are invalid.")
    if not isinstance(plan.get("acceptance_criteria"), list) or not plan.get("acceptance_criteria") or any(not isinstance(item, str) or not item.strip() for item in plan.get("acceptance_criteria", [])):
        add("PLAN_ACCEPTANCE_INVALID", "At least one resolved acceptance criterion is required.")
    provenance = plan.get("provenance")
    if not isinstance(provenance, dict) or set(provenance) != {"collector", "collector_version", "generated_utc"} or provenance.get("collector") != "create_siesta_plan.py" or provenance.get("collector_version") != TOOL_VERSION:
        add("PLAN_PROVENANCE_INVALID", "The plan provenance is invalid.")
    return findings


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise ValueError("refusing to overwrite an existing scientific plan")
    if not path.parent.is_dir():
        raise ValueError("plan output parent directory does not exist")
    rendered = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        handle.write(rendered)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--protocol-id", required=True)
    parser.add_argument("--state-id", required=True)
    parser.add_argument("--task-type", choices=sorted(TASK_WORKFLOWS), required=True)
    parser.add_argument("--siesta-version", required=True)
    parser.add_argument("--periodicity", choices=PERIODICITIES, required=True)
    parser.add_argument("--workflow-stage", choices=WORKFLOW_STAGES, required=True)
    parser.add_argument("--objective", required=True)
    parser.add_argument("--observable", required=True)
    parser.add_argument("--observable-unit", required=True)
    parser.add_argument("--normalization", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--absolute-tolerance", type=float)
    parser.add_argument("--relative-tolerance", type=float)
    parser.add_argument("--acceptance-criterion", action="append", default=[])
    parser.add_argument("--feature", action="append", default=[])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        payload = build_plan(
            case_id=args.case_id,
            protocol_id=args.protocol_id,
            state_id=args.state_id,
            task_type=args.task_type,
            siesta_version=args.siesta_version,
            periodicity=args.periodicity,
            workflow_stage=args.workflow_stage,
            objective=args.objective,
            observable=args.observable,
            observable_unit=args.observable_unit,
            normalization=args.normalization,
            reference=args.reference,
            absolute_tolerance=args.absolute_tolerance,
            relative_tolerance=args.relative_tolerance,
            acceptance_criteria=args.acceptance_criterion,
            features=args.feature,
        )
        findings = validate_plan(payload)
        if findings:
            raise ValueError("generated plan failed self-validation")
        atomic_write(args.out, payload)
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"decision": "block", "error_type": type(exc).__name__, "message": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
