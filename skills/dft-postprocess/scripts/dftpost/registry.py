from __future__ import annotations

from pathlib import Path
import re
import sys
from typing import Any, Iterable


for _parent in Path(__file__).resolve().parents:
    if _parent.joinpath("tools", "registry_snapshot.py").is_file():
        _tools = str(_parent / "tools")
        if _tools not in sys.path:
            sys.path.insert(0, _tools)
        break
else:  # pragma: no cover - installation layout is checked by the caller
    raise RuntimeError("cannot locate shared registry snapshot loader")

from registry_snapshot import (  # noqa: E402
    RegistrySnapshot,
    RegistrySnapshotError,
    load_registry_snapshot,
)
from registry_yaml import load_yaml_strict  # noqa: E402


MATURITY_LEVELS = (
    "design-only",
    "synthetic-validated",
    "format-fixture-validated",
    "real-artifact-validated",
    "tool-integration-validated",
)
BACKEND_KINDS = {"builtin-python", "python-package", "external-executable"}
OBSERVABLE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ABSOLUTE_PRIVATE_PATH = re.compile(r"(?:^|[\s`'\"])(?:/home/|/Users/|[A-Za-z]:\\)")


def registry_path() -> Path:
    return Path(__file__).resolve().parents[2] / "references" / "observable-registry.yaml"


def software_registry_path() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "registry" / "software-registry.yaml"
        if candidate.is_file() and parent.joinpath("skills").is_dir():
            return candidate
    raise RuntimeError("cannot locate registry/software-registry.yaml")


def _snapshot(snapshot: RegistrySnapshot | None = None) -> RegistrySnapshot:
    return snapshot or load_registry_snapshot(software_registry_path().parents[1])


def registered_codes(snapshot: RegistrySnapshot | None = None) -> tuple[str, ...]:
    return _snapshot(snapshot).calculation_codes()


def registered_aggregate_codes(snapshot: RegistrySnapshot | None = None) -> tuple[str, ...]:
    return _snapshot(snapshot).aggregate_codes()


def load_registry(path: Path | None = None) -> dict[str, Any]:
    selected = path or registry_path()
    return load_yaml_strict(selected, "observable-registry.yaml")


def _strings(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _strings(key)
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def validate_registry(
    data: object,
    *,
    snapshot: RegistrySnapshot | None = None,
) -> list[str]:
    failures: list[str] = []
    if not isinstance(data, dict):
        return ["<root>: registry must be a mapping"]
    if data.get("schema_version") != "1.0":
        failures.append("schema_version: expected '1.0'")
    if tuple(data.get("maturity_levels", ())) != MATURITY_LEVELS:
        failures.append("maturity_levels: expected the canonical ordered levels")

    backends = data.get("backends")
    if not isinstance(backends, dict) or not backends:
        failures.append("backends: expected a nonempty mapping")
        backends = {}
    else:
        for backend_id, specification in sorted(backends.items()):
            if not isinstance(specification, dict):
                failures.append(f"backends/{backend_id}: expected a mapping")
                continue
            if specification.get("kind") not in BACKEND_KINDS:
                failures.append(f"backends/{backend_id}/kind: unsupported backend kind")
            implemented = specification.get("implemented", False)
            if not isinstance(implemented, bool):
                failures.append(f"backends/{backend_id}/implemented: expected boolean when present")
            capability = specification.get("capability_key")
            if capability is not None and not isinstance(capability, str):
                failures.append(f"backends/{backend_id}/capability_key: expected string or null")

    try:
        supported_codes = set(registered_codes(snapshot))
    except (OSError, RuntimeError, RegistrySnapshotError, ValueError) as exc:
        failures.append(f"software-registry: {exc}")
        supported_codes = set()

    observables = data.get("observables")
    if not isinstance(observables, dict) or not observables:
        failures.append("observables: expected a nonempty mapping")
        observables = {}
    required_fields = {"title", "scope", "dataset_kind", "validators", "analyses", "plots", "codes"}
    for observable_id, observable in sorted(observables.items()):
        location = f"observables/{observable_id}"
        if not isinstance(observable_id, str) or not OBSERVABLE_ID.fullmatch(observable_id):
            failures.append(f"{location}: invalid observable id")
        if not isinstance(observable, dict):
            failures.append(f"{location}: expected a mapping")
            continue
        missing = sorted(required_fields.difference(observable))
        if missing:
            failures.append(f"{location}: missing fields {missing}")
        for field in ("validators", "analyses", "plots"):
            values = observable.get(field)
            if not isinstance(values, list) or not all(isinstance(item, str) and item for item in values):
                failures.append(f"{location}/{field}: expected a string list")
        codes = observable.get("codes")
        if not isinstance(codes, dict) or not codes:
            failures.append(f"{location}/codes: expected a nonempty mapping")
            continue
        for code, route in sorted(codes.items()):
            route_location = f"{location}/codes/{code}"
            if code not in supported_codes:
                failures.append(f"{route_location}: unsupported DFT code")
            if not isinstance(route, dict):
                failures.append(f"{route_location}: expected a mapping")
                continue
            maturity = route.get("maturity")
            if maturity not in MATURITY_LEVELS:
                failures.append(f"{route_location}/maturity: unknown maturity {maturity!r}")
            evidence = route.get("required_evidence")
            if not isinstance(evidence, list) or not evidence or not all(isinstance(item, str) and item for item in evidence):
                failures.append(f"{route_location}/required_evidence: expected a nonempty string list")
            parameters = route.get("required_parameters", [])
            if not isinstance(parameters, list) or not all(isinstance(item, str) and OBSERVABLE_ID.fullmatch(item) for item in parameters):
                failures.append(f"{route_location}/required_parameters: expected an optional observable-id-style string list")
            route_backends = route.get("backends")
            if not isinstance(route_backends, list) or not route_backends:
                failures.append(f"{route_location}/backends: expected a nonempty list")
            else:
                for backend_id in route_backends:
                    if backend_id not in backends:
                        failures.append(f"{route_location}/backends: unknown backend {backend_id!r}")

    if any(ABSOLUTE_PRIVATE_PATH.search(value) for value in _strings(data)):
        failures.append("<root>: registry contains non-general content such as a real absolute path")
    return failures


def get_observable(observable_id: str, path: Path | None = None) -> dict[str, Any]:
    registry = load_registry(path)
    failures = validate_registry(registry)
    if failures:
        raise ValueError("invalid observable registry: " + "; ".join(failures))
    try:
        return registry["observables"][observable_id]
    except KeyError as exc:
        raise KeyError(f"unknown observable: {observable_id}") from exc
