from __future__ import annotations

import ast
import hashlib
from functools import lru_cache
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
SHA256 = re.compile(r"^[0-9a-f]{64}$")
ABSOLUTE_PRIVATE_PATH = re.compile(r"(?:^|[\s`'\"])(?:/home/|/Users/|[A-Za-z]:\\)")
EVIDENCE_CLASS_CEILINGS = {
    "synthetic": "synthetic-validated",
    "format-fixture": "format-fixture-validated",
    "real-artifact": "real-artifact-validated",
    "tool-integration": "tool-integration-validated",
}
CANONICAL_VALIDATION_COMMAND = [
    "python3",
    "-m",
    "unittest",
    "discover",
    "-s",
    "tests",
    "-v",
]


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


def _repository_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if parent.joinpath("skills", "dft-postprocess").is_dir() and parent.joinpath("tests").is_dir():
            return parent
    raise RuntimeError("cannot locate repository root for validation evidence")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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

    validation_evidence = data.get("validation_evidence")
    if not isinstance(validation_evidence, dict) or not validation_evidence:
        failures.append("validation_evidence: expected a nonempty mapping")
        validation_evidence = {}
    else:
        try:
            root = _repository_root()
        except RuntimeError as exc:
            failures.append(f"validation_evidence: {exc}")
            root = None
        for evidence_id, evidence in sorted(validation_evidence.items()):
            location = f"validation_evidence/{evidence_id}"
            if not isinstance(evidence_id, str) or not OBSERVABLE_ID.fullmatch(evidence_id):
                failures.append(f"{location}: invalid evidence id")
            if not isinstance(evidence, dict):
                failures.append(f"{location}: expected a mapping")
                continue
            evidence_class = evidence.get("evidence_class")
            if evidence_class not in EVIDENCE_CLASS_CEILINGS:
                failures.append(f"{location}/evidence_class: unsupported evidence class")
            relative_text = evidence.get("path")
            if not isinstance(relative_text, str) or not relative_text:
                failures.append(f"{location}/path: expected a nonempty repository-relative path")
                candidate = None
            else:
                relative = Path(relative_text)
                if relative.is_absolute() or ".." in relative.parts:
                    failures.append(f"{location}/path: expected a safe repository-relative path")
                    candidate = None
                else:
                    candidate = root / relative if root is not None else None
                    if not relative.parts or relative.parts[0] != "tests" or not relative.name.startswith("test_"):
                        failures.append(f"{location}/path: evidence must be a discovered root unittest module")
                    if candidate is not None and not candidate.is_file():
                        failures.append(f"{location}/path: evidence file is missing")
                        candidate = None
            expected_sha256 = evidence.get("sha256")
            if not isinstance(expected_sha256, str) or not SHA256.fullmatch(expected_sha256):
                failures.append(f"{location}/sha256: expected lowercase SHA-256")
            elif candidate is not None and _sha256(candidate) != expected_sha256:
                failures.append(f"{location}/sha256: evidence file hash mismatch")
            test_ids = evidence.get("test_ids")
            if not isinstance(test_ids, list) or not test_ids or not all(
                isinstance(item, str) and item.startswith("test_") for item in test_ids
            ):
                failures.append(f"{location}/test_ids: expected a nonempty test-id list")
            elif candidate is not None:
                source = candidate.read_text(encoding="utf-8", errors="replace")
                try:
                    discovered_tests = {
                        node.name for node in ast.walk(ast.parse(source)) if isinstance(node, ast.FunctionDef)
                    }
                except SyntaxError:
                    discovered_tests = set()
                    failures.append(f"{location}/path: evidence test source is not valid Python")
                for test_id in test_ids:
                    if test_id not in discovered_tests:
                        failures.append(f"{location}/test_ids: missing test {test_id!r}")
            if evidence.get("command") != CANONICAL_VALIDATION_COMMAND:
                failures.append(
                    f"{location}/command: expected the canonical CI unittest discovery command"
                )
            expected_result = evidence.get("expected_result")
            if expected_result != {"status": "pass", "return_code": 0}:
                failures.append(
                    f"{location}/expected_result: expected pass with return_code 0"
                )
            target_tests = evidence.get("target_tests")
            if not isinstance(target_tests, dict) or not target_tests:
                failures.append(f"{location}/target_tests: expected backend-target to test-id mapping")
            else:
                mapped_test_ids: set[str] = set()
                for target, mapped_tests in sorted(target_tests.items()):
                    if not isinstance(target, str) or target.count("/") != 2:
                        failures.append(f"{location}/target_tests: invalid backend target {target!r}")
                    if not isinstance(mapped_tests, list) or not mapped_tests or not all(
                        isinstance(item, str) and item in (test_ids if isinstance(test_ids, list) else [])
                        for item in mapped_tests
                    ):
                        failures.append(
                            f"{location}/target_tests/{target}: expected registered test ids"
                        )
                    else:
                        mapped_test_ids.update(mapped_tests)
                if isinstance(test_ids, list) and mapped_test_ids != set(test_ids):
                    failures.append(
                        f"{location}/test_ids: every test id must map to at least one backend target"
                    )

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
        supported_codes = set(registered_codes(snapshot)).union(registered_aggregate_codes(snapshot))
    except (OSError, RuntimeError, RegistrySnapshotError, ValueError) as exc:
        failures.append(f"software-registry: {exc}")
        supported_codes = set()

    observables = data.get("observables")
    if not isinstance(observables, dict) or not observables:
        failures.append("observables: expected a nonempty mapping")
        observables = {}
    required_fields = {"title", "scope", "dataset_kind", "validators", "analyses", "plots", "codes"}
    known_backend_targets: set[str] = set()
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
                route_backends = []
            else:
                for backend_id in route_backends:
                    if backend_id not in backends:
                        failures.append(f"{route_location}/backends: unknown backend {backend_id!r}")
            backend_routes = route.get("backend_routes")
            if not isinstance(backend_routes, dict) or not backend_routes:
                failures.append(f"{route_location}/backend_routes: expected a nonempty mapping")
                continue
            if set(backend_routes) != set(route_backends):
                failures.append(f"{route_location}/backend_routes: keys must exactly match backends")
            route_maturities: list[str] = []
            for backend_id, backend_route in sorted(backend_routes.items()):
                backend_location = f"{route_location}/backend_routes/{backend_id}"
                backend_target = f"{observable_id}/{code}/{backend_id}"
                known_backend_targets.add(backend_target)
                if not isinstance(backend_route, dict):
                    failures.append(f"{backend_location}: expected a mapping")
                    continue
                backend_maturity = backend_route.get("maturity")
                if backend_maturity not in MATURITY_LEVELS:
                    failures.append(f"{backend_location}/maturity: unknown maturity {backend_maturity!r}")
                    continue
                route_maturities.append(backend_maturity)
                backend_specification = backends.get(backend_id)
                if (
                    isinstance(backend_specification, dict)
                    and not backend_specification.get("implemented", False)
                    and backend_maturity != "design-only"
                ):
                    failures.append(f"{backend_location}/maturity: unimplemented backend must be design-only")
                evidence_ref = backend_route.get("evidence_ref")
                if backend_maturity == "design-only":
                    if evidence_ref is not None:
                        failures.append(f"{backend_location}/evidence_ref: design-only route must not claim validation evidence")
                    continue
                if not isinstance(evidence_ref, str) or not evidence_ref:
                    failures.append(f"{backend_location}/evidence_ref: non-design maturity requires evidence_ref")
                    continue
                evidence = validation_evidence.get(evidence_ref)
                if not isinstance(evidence, dict):
                    failures.append(f"{backend_location}/evidence_ref: unknown validation evidence {evidence_ref!r}")
                    continue
                if backend_target not in evidence.get("target_tests", {}):
                    failures.append(
                        f"{backend_location}/evidence_ref: evidence does not map exact backend target"
                    )
                ceiling = EVIDENCE_CLASS_CEILINGS.get(evidence.get("evidence_class"))
                if (
                    ceiling in MATURITY_LEVELS
                    and MATURITY_LEVELS.index(backend_maturity) > MATURITY_LEVELS.index(ceiling)
                ):
                    failures.append(
                        f"{backend_location}/maturity: exceeds evidence ceiling {ceiling!r}"
                    )
            if route_maturities:
                computed = max(route_maturities, key=MATURITY_LEVELS.index)
                if maturity in MATURITY_LEVELS and maturity != computed:
                    failures.append(
                        f"{route_location}/maturity: legacy summary must equal backend-route maximum {computed!r}"
                    )

    for evidence_id, evidence in sorted(validation_evidence.items()):
        if not isinstance(evidence, dict):
            continue
        for target in evidence.get("target_tests", {}):
            if isinstance(target, str) and target not in known_backend_targets:
                failures.append(
                    f"validation_evidence/{evidence_id}/target_tests: unknown backend target {target!r}"
                )

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


@lru_cache(maxsize=1)
def _validated_canonical_registry() -> dict[str, Any]:
    registry = load_registry()
    failures = validate_registry(registry)
    if failures:
        raise ValueError("invalid observable registry: " + "; ".join(failures))
    return registry


def get_backend_route(
    observable_id: str,
    code: str,
    backend_id: str,
    path: Path | None = None,
) -> dict[str, Any]:
    registry = _validated_canonical_registry() if path is None else load_registry(path)
    if path is not None:
        failures = validate_registry(registry)
        if failures:
            raise ValueError("invalid observable registry: " + "; ".join(failures))
    try:
        return dict(
            registry["observables"][observable_id]["codes"][code]["backend_routes"][backend_id]
        )
    except KeyError as exc:
        raise KeyError(f"unknown backend route: {observable_id}/{code}/{backend_id}") from exc


def resolve_backend_maturity(
    observable_id: str,
    code: str,
    backend_id: str,
    requested: str | None = None,
) -> str:
    route = get_backend_route(observable_id, code, backend_id)
    registered = route["maturity"]
    if registered == "design-only":
        raise ValueError(f"backend route is design-only: {observable_id}/{code}/{backend_id}")
    if requested is None:
        return registered
    if requested not in MATURITY_LEVELS:
        raise ValueError(f"unknown maturity: {requested}")
    if MATURITY_LEVELS.index(requested) > MATURITY_LEVELS.index(registered):
        raise ValueError(
            "requested maturity exceeds registered backend maturity: "
            f"{requested} > {registered} for {observable_id}/{code}/{backend_id}"
        )
    return requested
