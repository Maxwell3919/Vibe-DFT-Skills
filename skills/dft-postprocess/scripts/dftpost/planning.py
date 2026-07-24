from __future__ import annotations

from pathlib import Path
from typing import Any

from . import __version__
from .manifests import validation_errors
from .registry import load_registry, validate_registry
from .utils import utc_now


def _builtin_step(
    observable_id: str,
    code: str,
    backend_id: str,
    source_files: list[dict[str, Any]],
    parameters: dict[str, str],
) -> tuple[list[str], list[str]]:
    evidence = {item["role"]: item["path"] for item in source_files if item["path"]}
    if observable_id == "run-trace":
        return (
            [
                "dftpost", "run-trace", evidence["main-output"], "--code", code,
                "--dataset-id", f"planned-{code}-run-trace-dataset", "--out-dir", ".",
            ],
            [
                "electronic-iterations.csv", "ionic-steps.csv", "run-trace.analysis.json",
                "run-trace.plot.json", "run-trace.dataset.json", "run-trace.png",
            ],
        )
    if observable_id == "bands" and code == "qe" and backend_id == "python.qe-bands":
        return (
            [
                "dftpost", "qe-bands", evidence["eigenvalues"],
                "--energy-reference", evidence["energy-reference"],
                "--dataset-id", "planned-bands-dataset", "--out-dir", ".",
            ],
            ["bands.csv", "bands.analysis.json", "bands.plot.json", "bands.dataset.json", "bands.png"],
        )
    if observable_id == "dos-pdos" and code == "qe" and backend_id == "python.qe-dos":
        return (
            [
                "dftpost", "qe-dos", evidence["dos-table"],
                "--energy-reference", evidence["energy-reference"],
                "--dataset-id", "planned-dos-dataset", "--out-dir", ".",
            ],
            ["dos.csv", "dos.analysis.json", "dos.plot.json", "dos.dataset.json", "dos.png"],
        )
    if observable_id == "bands" and code == "vasp" and backend_id == "python.vasp-bands":
        return (
            [
                "dftpost", "vasp-bands",
                "--eigenval", evidence["eigenvalues"],
                "--kpoints", evidence["k-path"],
                "--poscar", evidence["structure"],
                "--outcar", evidence["energy-reference"],
                "--dataset-id", "planned-vasp-bands-dataset", "--out-dir", ".",
            ],
            ["bands.csv", "bands.analysis.json", "bands.plot.json", "bands.dataset.json", "bands.png"],
        )
    if observable_id == "dos-pdos" and code == "vasp" and backend_id == "python.vasp-dos":
        return (
            [
                "dftpost", "vasp-dos",
                "--doscar", evidence["dos-data"],
                "--poscar", evidence["structure"],
                "--outcar", evidence["energy-reference"],
                "--dataset-id", "planned-vasp-dos-dataset", "--out-dir", ".",
            ],
            ["dos.csv", "dos.analysis.json", "dos.plot.json", "dos.dataset.json", "dos.png"],
        )
    if observable_id == "phonon" and code == "qe" and backend_id == "python.qe-phonon":
        return (
            [
                "dftpost", "qe-phonon", evidence["phonon-frequencies"],
                "--frequency-unit", parameters["frequency-unit"],
                "--dataset-id", "planned-qe-phonon-dataset", "--out-dir", ".",
            ],
            ["phonon.csv", "phonon.analysis.json", "phonon.plot.json", "phonon.dataset.json", "phonon.png"],
        )
    if observable_id == "real-space" and backend_id == "python.grid":
        return (
            [
                "dftpost", "grid-field", evidence["grid-field"], "--code", code,
                "--field-kind", parameters["field-kind"], "--field-unit", parameters["field-unit"],
                "--dataset-id", f"planned-{code}-real-space-dataset", "--out-dir", ".",
            ],
            [
                "planar-average.csv", "slice.csv", "real-space.analysis.json",
                "real-space.plot.json", "real-space.dataset.json", "real-space.png",
            ],
        )
    if observable_id == "neb" and backend_id == "python.neb":
        return (
            [
                "dftpost", "neb-table", evidence["neb-table"], "--code", code,
                "--coordinate-column", parameters["coordinate-column"],
                "--energy-column", parameters["energy-column"],
                "--coordinate-unit", parameters["coordinate-unit"],
                "--energy-unit", parameters["energy-unit"],
                "--reference", parameters["reference"],
                "--dataset-id", f"planned-{code}-neb-dataset", "--out-dir", ".",
            ],
            ["neb.csv", "neb.analysis.json", "neb.plot.json", "neb.dataset.json", "neb.png"],
        )
    if observable_id == "optical" and backend_id == "python.optical":
        component_arguments: list[str] = []
        for specification in parameters["components"].split(";"):
            component_arguments.extend(["--component", specification])
        return (
            [
                "dftpost", "optical-table", evidence["dielectric-data"], "--code", code,
                "--energy-column", parameters["energy-column"],
                *component_arguments,
                "--broadening", parameters["broadening"],
                "--dataset-id", f"planned-{code}-optical-dataset", "--out-dir", ".",
            ],
            ["optical.csv", "optical.analysis.json", "optical.plot.json", "optical.dataset.json", "optical.png"],
        )
    if observable_id == "epc" and code == "qe" and backend_id == "python.qe-epc":
        return (
            [
                "dftpost", "qe-epc", "--alpha2f", evidence["epc-table"],
                "--lambda-table", evidence["smearing-definition"],
                "--dataset-id", "planned-qe-epc-dataset", "--out-dir", ".",
            ],
            ["alpha2f.csv", "smearing-series.csv", "epc.analysis.json", "epc.plot.json", "epc.dataset.json", "epc.png"],
        )
    raise ValueError(f"implemented backend lacks a planner route: {observable_id}/{code}/{backend_id}")


def _backend_available(specification: dict[str, Any], capabilities: dict[str, Any]) -> bool:
    kind = specification["kind"]
    capability_key = specification.get("capability_key")
    if kind == "builtin-python":
        return True
    if kind == "python-package":
        return bool(capabilities.get("python_packages", {}).get(capability_key, {}).get("available"))
    if kind == "external-executable":
        return bool(capabilities.get("external_tools", {}).get(capability_key, {}).get("available"))
    return False


def _evidence_record(root: Path, role: str, value: str | None) -> tuple[dict[str, Any], str | None]:
    if value is None:
        return {"role": role, "path": None, "required": True, "present": False}, f"missing required evidence: {role}"
    relative = Path(value)
    if relative.is_absolute():
        raise ValueError(f"evidence paths must be relative to the source root: {value}")
    candidate = (root / relative).resolve()
    try:
        normalized = candidate.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError(f"evidence path escapes the source root: {value}") from exc
    if candidate.name == "POTCAR":
        raise ValueError("POTCAR contents must not be used as postprocessing evidence")
    present = candidate.is_file()
    blocker = None if present else f"missing required evidence: {role} ({normalized})"
    return {"role": role, "path": normalized, "required": True, "present": present}, blocker


def build_postprocess_plan(
    plan_id: str,
    observable_id: str,
    code: str,
    source_root: Path,
    output_root: Path,
    evidence: dict[str, str],
    capabilities: dict[str, Any],
    parameters: dict[str, str] | None = None,
) -> dict[str, Any]:
    source_root = source_root.resolve()
    output_root = output_root.resolve()
    if not source_root.is_dir():
        raise ValueError(f"source root is not a directory: {source_root}")
    if source_root == output_root:
        raise ValueError("output root must be separate from the source root")

    registry = load_registry()
    registry_failures = validate_registry(registry)
    if registry_failures:
        raise ValueError("invalid observable registry: " + "; ".join(registry_failures))
    try:
        observable = registry["observables"][observable_id]
        route = observable["codes"][code]
    except KeyError as exc:
        raise ValueError(f"unsupported observable/code route: {observable_id}/{code}") from exc

    parameters = dict(parameters or {})
    blockers: list[str] = []
    source_files = []
    for role in route["required_evidence"]:
        record, blocker = _evidence_record(source_root, role, evidence.get(role))
        source_files.append(record)
        if blocker:
            blockers.append(blocker)
    for name in route.get("required_parameters", []):
        value = parameters.get(name)
        if value is None or not value.strip():
            blockers.append(f"missing required parameter: {name}")

    if route["maturity"] == "design-only":
        blockers.append(f"workflow maturity is design-only: {observable_id}/{code}")

    selected_backend = None
    available_design_backend = None
    for backend_id in route["backends"]:
        specification = registry["backends"][backend_id]
        if not specification.get("implemented", False):
            continue
        available = _backend_available(specification, capabilities)
        if available:
            candidate = {
                "id": backend_id,
                "kind": specification["kind"],
                "maturity": route["backend_routes"][backend_id]["maturity"],
                "available": True,
            }
            if candidate["maturity"] == "design-only":
                available_design_backend = available_design_backend or candidate
                continue
            selected_backend = candidate
            break
    selected_backend = selected_backend or available_design_backend
    if selected_backend is None:
        blockers.append(f"no implemented available backend: {observable_id}/{code}")
    elif selected_backend["maturity"] == "design-only":
        blockers.append(
            f"backend maturity is design-only: {observable_id}/{code}/{selected_backend['id']}"
        )

    steps = []
    if not blockers and selected_backend is not None:
        action = "python" if selected_backend["kind"] != "external-executable" else "external"
        command, outputs = _builtin_step(observable_id, code, selected_backend["id"], source_files, parameters)
        steps.append(
            {
                "step_id": "extract-01",
                "operation": f"extract-{observable_id}",
                "adapter": selected_backend["id"],
                "action": action,
                "command": command,
                "inputs": [item["path"] for item in source_files if item["path"]],
                "outputs": outputs,
                "timeout_s": 300,
                "overwrite": False,
            }
        )

    plan = {
        "schema_version": "1.0",
        "plan_id": plan_id,
        "observable": observable_id,
        "code": code,
        "status": "blocked" if blockers else "planned",
        "source_root_label": source_root.name,
        "output_root_label": output_root.name,
        "source_files": source_files,
        "parameters": parameters,
        "backend": selected_backend,
        "steps": steps,
        "blockers": blockers,
        "provenance": {"planner": "dftpost", "planner_version": __version__, "generated_utc": utc_now()},
    }
    errors = validation_errors("plan", plan)
    if errors:
        raise ValueError("generated postprocess plan is invalid: " + "; ".join(errors))
    return plan
