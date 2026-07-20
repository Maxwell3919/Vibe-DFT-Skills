#!/usr/bin/env python3
"""Migrate one record between contract versions without synthesizing scientific evidence."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tempfile
import sys
from typing import Any, Iterable, Sequence

import strict_json
import validate_contract


MAX_BYTES = 16 * 1024 * 1024
CLAIM_ORDER = {
    "no_positive_claim": 0,
    "documented_behavior_only": 1,
    "input_gates_only": 2,
    "technical_run_gates_only": 3,
    "numerical_candidate_only": 4,
    "eligible_for_expert_review": 5,
}
CLAIM_KEYS = frozenset({"claim_ceiling", "maximum_claim"})
PROTECTED_KEYS = frozenset(
    {
        "claim_ceiling",
        "maximum_claim",
        "status",
        "decision",
        "evidence",
        "validation",
        "scientific_acceptance",
        "physical_validity",
        "numerical_convergence",
        "execution_status",
        "reviewer",
        "sha256",
        "source_tree_sha256",
    }
)


@dataclass(frozen=True, order=True)
class Finding:
    code: str
    location: str
    message: str

    def render(self) -> str:
        return f"{self.code}\t{self.location}\t{self.message}"


class MigrationError(ValueError):
    def __init__(self, code: str, location: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.location = location
        self.message = message

    def finding(self) -> Finding:
        return Finding(self.code, self.location, self.message)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _safe_relative(value: object) -> PurePosixPath | None:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path


def _resolve(root: Path, value: object, label: str) -> Path:
    relative = _safe_relative(value)
    if relative is None:
        raise MigrationError("MIGRATION_PATH_INVALID", label, f"unsafe path {value!r}")
    target = root.joinpath(*relative.parts)
    try:
        target.resolve(strict=False).relative_to(root.resolve())
    except ValueError as exc:
        raise MigrationError("MIGRATION_PATH_ESCAPE", label, str(value)) from exc
    return target


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _decode_pointer(pointer: object) -> tuple[str, ...]:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise MigrationError("MIGRATION_POINTER_INVALID", str(pointer), "JSON Pointer must start with '/'")
    parts = pointer[1:].split("/")
    if not parts or any(part == "" for part in parts):
        raise MigrationError("MIGRATION_POINTER_INVALID", pointer, "empty JSON Pointer segments are forbidden")
    decoded = []
    for part in parts:
        index = 0
        output = []
        while index < len(part):
            if part[index] != "~":
                output.append(part[index])
                index += 1
                continue
            if index + 1 >= len(part) or part[index + 1] not in {"0", "1"}:
                raise MigrationError("MIGRATION_POINTER_INVALID", pointer, "invalid JSON Pointer escape")
            output.append("~" if part[index + 1] == "0" else "/")
            index += 2
        decoded.append("".join(output))
    return tuple(decoded)


def _encode_pointer(parts: Iterable[object]) -> str:
    encoded = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(encoded)


def _get(container: object, parts: Sequence[str], pointer: str) -> object:
    current = container
    for part in parts:
        if isinstance(current, dict):
            if part not in current:
                raise MigrationError("MIGRATION_SOURCE_POINTER_MISSING", pointer, "field does not exist")
            current = current[part]
        elif isinstance(current, list):
            if not part.isdigit() or int(part) >= len(current):
                raise MigrationError("MIGRATION_SOURCE_POINTER_MISSING", pointer, "list index does not exist")
            current = current[int(part)]
        else:
            raise MigrationError("MIGRATION_SOURCE_POINTER_MISSING", pointer, "pointer crosses a scalar value")
    return current


def _parent(container: object, parts: Sequence[str], pointer: str, *, create: bool) -> tuple[object, str]:
    if not parts:
        raise MigrationError("MIGRATION_POINTER_INVALID", pointer, "root replacement is forbidden")
    current = container
    for part in parts[:-1]:
        if isinstance(current, dict):
            if part not in current:
                if not create:
                    raise MigrationError("MIGRATION_TARGET_PARENT_MISSING", pointer, "target parent is absent")
                current[part] = {}
            child = current[part]
            if not isinstance(child, (dict, list)):
                raise MigrationError("MIGRATION_TARGET_PARENT_INVALID", pointer, "target parent crosses a scalar")
            current = child
        elif isinstance(current, list):
            if not part.isdigit() or int(part) >= len(current):
                raise MigrationError("MIGRATION_TARGET_PARENT_MISSING", pointer, "list parent index is absent")
            current = current[int(part)]
        else:
            raise MigrationError("MIGRATION_TARGET_PARENT_INVALID", pointer, "target parent crosses a scalar")
    return current, parts[-1]


def _set(container: object, pointer: str, value: object) -> None:
    parts = _decode_pointer(pointer)
    parent, key = _parent(container, parts, pointer, create=True)
    if isinstance(parent, dict):
        if key in parent:
            raise MigrationError("MIGRATION_TARGET_EXISTS", pointer, "target field already exists")
        parent[key] = value
    elif isinstance(parent, list):
        if not key.isdigit() or int(key) > len(parent):
            raise MigrationError("MIGRATION_TARGET_INDEX_INVALID", pointer, "target list index is invalid")
        if int(key) != len(parent):
            raise MigrationError("MIGRATION_TARGET_EXISTS", pointer, "overwriting list items is forbidden")
        parent.append(value)
    else:
        raise MigrationError("MIGRATION_TARGET_PARENT_INVALID", pointer, "target parent is scalar")


def _remove(container: object, pointer: str) -> object:
    parts = _decode_pointer(pointer)
    parent, key = _parent(container, parts, pointer, create=False)
    if isinstance(parent, dict):
        if key not in parent:
            raise MigrationError("MIGRATION_SOURCE_POINTER_MISSING", pointer, "field does not exist")
        return parent.pop(key)
    if isinstance(parent, list):
        if not key.isdigit() or int(key) >= len(parent):
            raise MigrationError("MIGRATION_SOURCE_POINTER_MISSING", pointer, "list index does not exist")
        return parent.pop(int(key))
    raise MigrationError("MIGRATION_SOURCE_POINTER_MISSING", pointer, "parent is scalar")


def _leaf(pointer: str) -> str:
    return _decode_pointer(pointer)[-1].lower()


def _protected(pointer: str) -> bool:
    return _leaf(pointer) in PROTECTED_KEYS


def _walk(value: object, path: tuple[object, ...] = ()) -> Iterable[tuple[tuple[object, ...], object]]:
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, (*path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, (*path, index))


def _protected_values(value: object) -> dict[str, object]:
    result: dict[str, object] = {}
    for path, child in _walk(value):
        if path and str(path[-1]).lower() in PROTECTED_KEYS:
            result[_encode_pointer(path)] = copy.deepcopy(child)
    return result


def _strongest_claim(value: object) -> str | None:
    found: list[str] = []
    for path, child in _walk(value):
        if path and str(path[-1]).lower() in CLAIM_KEYS and isinstance(child, str):
            if child not in CLAIM_ORDER:
                raise MigrationError(
                    "MIGRATION_CLAIM_CEILING_UNKNOWN",
                    _encode_pointer(path),
                    f"unknown claim ceiling {child!r}",
                )
            found.append(child)
    return max(found, key=CLAIM_ORDER.__getitem__) if found else None


def _record_id(data: dict[str, Any], contract: validate_contract.ContractSchema) -> str | None:
    field = contract.record_id_field
    value = data.get(field) if field else None
    return value if isinstance(value, str) else None


def _validation_findings(
    selector: str,
    data: dict[str, Any],
    contracts_dir: Path,
    prefix: str,
) -> list[Finding]:
    return [
        Finding("MIGRATION_SCHEMA_INVALID", prefix, error)
        for error in validate_contract.validation_errors(selector, data, contracts_dir)
    ]


def _atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def migrate(
    root: Path,
    plan_path: Path,
    *,
    contracts_dir: Path | None = None,
    write: bool = True,
) -> tuple[list[Finding], dict[str, Any], dict[str, Any] | None]:
    root = root.resolve()
    contracts = (contracts_dir or root / "contracts").resolve()
    findings: list[Finding] = []
    try:
        plan_raw = plan_path.read_bytes()
        plan = strict_json.loads_object(plan_raw, plan_path.name, max_bytes=MAX_BYTES)
    except (OSError, strict_json.StrictJSONError) as exc:
        return [Finding("MIGRATION_PLAN_INVALID", str(plan_path), str(exc))], {}, None
    findings.extend(_validation_findings("contract-migration-plan@1.0", plan, contracts, "plan"))
    if findings:
        return sorted(set(findings)), {}, None

    source_identity = plan["source_contract"]
    target_identity = plan["target_contract"]
    source_selector = f"{source_identity['name']}@{source_identity['version']}"
    target_selector = f"{target_identity['name']}@{target_identity['version']}"
    if source_identity["name"] != target_identity["name"]:
        findings.append(
            Finding("MIGRATION_CONTRACT_NAME_CHANGED", "target_contract/name", "cross-contract migration is forbidden")
        )
    if source_selector == target_selector:
        findings.append(
            Finding("MIGRATION_VERSION_UNCHANGED", "target_contract/version", "source and target versions must differ")
        )
    try:
        catalog = validate_contract.load_catalog(contracts)
        source_contract = catalog.resolve(source_selector)
        target_contract = catalog.resolve(target_selector)
    except (validate_contract.CatalogError, validate_contract.ContractSelectionError, OSError, ValueError) as exc:
        findings.append(Finding("MIGRATION_CONTRACT_UNRESOLVED", "contracts", str(exc)))
        return sorted(set(findings)), {}, None
    if source_contract.document_kind != "content-addressed-record" or target_contract.document_kind != "content-addressed-record":
        findings.append(
            Finding("MIGRATION_RECORD_KIND_UNSUPPORTED", "contracts", "both contracts must be content-addressed records")
        )

    try:
        source_path = _resolve(root, plan["source_path"], "source_path")
        output_path = _resolve(root, plan["output_path"], "output_path")
        migration_path = _resolve(root, plan["migration_record_path"], "migration_record_path")
        plan_relative = plan_path.resolve().relative_to(root).as_posix()
    except (MigrationError, ValueError) as exc:
        finding = exc.finding() if isinstance(exc, MigrationError) else Finding("MIGRATION_PLAN_PATH_OUTSIDE_ROOT", str(plan_path), str(exc))
        findings.append(finding)
        return sorted(set(findings)), {}, None
    if len({source_path, output_path, migration_path, plan_path.resolve()}) != 4:
        findings.append(
            Finding("MIGRATION_PATH_COLLISION", "paths", "source, plan, output, and migration record paths must be distinct")
        )
    if output_path.exists() or migration_path.exists():
        findings.append(
            Finding("MIGRATION_OUTPUT_EXISTS", "paths", "migration never overwrites an existing output")
        )
    try:
        source_raw = source_path.read_bytes()
        source = strict_json.loads_object(source_raw, source_path.name, max_bytes=MAX_BYTES)
    except (OSError, strict_json.StrictJSONError) as exc:
        findings.append(Finding("MIGRATION_SOURCE_INVALID", str(source_path), str(exc)))
        return sorted(set(findings)), {}, None
    findings.extend(_validation_findings(source_selector, source, contracts, "source"))
    if findings:
        return sorted(set(findings)), {}, None

    protected_before = _protected_values(source)
    claim_before: str | None
    try:
        claim_before = _strongest_claim(source)
    except MigrationError as exc:
        findings.append(exc.finding())
        return sorted(set(findings)), {}, None
    target = copy.deepcopy(source)
    removed: list[str] = []
    try:
        for index, operation in enumerate(plan["operations"]):
            op = operation["op"]
            source_pointer = operation["from"]
            if _protected(source_pointer) and op in {"remove", "rename"}:
                raise MigrationError(
                    "MIGRATION_PROTECTED_FIELD_MUTATION",
                    f"operations/{index}",
                    f"{op} is forbidden for protected field {source_pointer}",
                )
            value = copy.deepcopy(_get(target, _decode_pointer(source_pointer), source_pointer))
            if op == "copy":
                _set(target, operation["to"], value)
            elif op == "rename":
                _set(target, operation["to"], value)
                _remove(target, source_pointer)
                removed.append(source_pointer)
            elif op == "remove":
                _remove(target, source_pointer)
                removed.append(source_pointer)
            else:
                raise MigrationError("MIGRATION_OPERATION_INVALID", f"operations/{index}", str(op))
    except MigrationError as exc:
        findings.append(exc.finding())
        return sorted(set(findings)), {}, None

    target["contract_name"] = target_contract.name
    target["schema_version"] = target_contract.version
    if target_contract.record_id_field is None:
        findings.append(
            Finding("MIGRATION_TARGET_RECORD_ID_UNAVAILABLE", "target_contract", "target has no content-addressed record ID field")
        )
    else:
        target[target_contract.record_id_field] = plan["target_record_id"]

    protected_after = _protected_values(target)
    for pointer, value in protected_before.items():
        if pointer not in protected_after or protected_after[pointer] != value:
            findings.append(
                Finding("MIGRATION_PROTECTED_FIELD_CHANGED", pointer, "protected evidence/status value was removed or changed")
            )
    try:
        claim_after = _strongest_claim(target)
    except MigrationError as exc:
        findings.append(exc.finding())
        claim_after = None
    if claim_before is not None:
        if claim_after is None:
            findings.append(
                Finding("MIGRATION_CLAIM_CEILING_REMOVED", "claim_ceiling", "source claim ceiling disappeared")
            )
        elif CLAIM_ORDER[claim_after] > CLAIM_ORDER[claim_before]:
            findings.append(
                Finding(
                    "MIGRATION_CLAIM_CEILING_INCREASED",
                    "claim_ceiling",
                    f"{claim_before} -> {claim_after}",
                )
            )
    findings.extend(_validation_findings(target_selector, target, contracts, "target"))
    if findings:
        return sorted(set(findings)), {}, target

    target_raw = (json.dumps(target, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    migration_id = f"{plan['plan_id']}-migration"
    migration_record = {
        "schema_version": "1.0",
        "contract_name": "contract-migration-record",
        "migration_id": migration_id,
        "plan_ref": {"path": plan_relative, "sha256": _sha256(plan_raw)},
        "source": {
            "path": plan["source_path"],
            "sha256": _sha256(source_raw),
            "contract": source_identity,
            "record_id": _record_id(source, source_contract),
        },
        "target": {
            "path": plan["output_path"],
            "sha256": _sha256(target_raw),
            "contract": target_identity,
            "record_id": _record_id(target, target_contract),
        },
        "operations": plan["operations"],
        "preserved_protected_pointers": sorted(protected_before),
        "removed_pointers": sorted(set(removed)),
        "evidence_boundary": {
            "scientific_values_synthesized": False,
            "protected_fields_preserved": True,
            "claim_ceiling_before": claim_before,
            "claim_ceiling_after": claim_after,
        },
        "validation": {"source_schema_valid": True, "target_schema_valid": True},
        "provenance": plan["provenance"],
    }
    findings.extend(
        _validation_findings(
            "contract-migration-record@1.0",
            migration_record,
            contracts,
            "migration_record",
        )
    )
    if findings:
        return sorted(set(findings)), migration_record, target
    migration_raw = (
        json.dumps(migration_record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    if write:
        try:
            _atomic_write(output_path, target_raw)
            _atomic_write(migration_path, migration_raw)
        except OSError as exc:
            output_path.unlink(missing_ok=True)
            migration_path.unlink(missing_ok=True)
            return [Finding("MIGRATION_WRITE_FAILED", "outputs", str(exc))], migration_record, target
    return [], migration_record, target


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--root", type=Path, default=repo_root())
    parser.add_argument("--contracts-dir", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    findings, migration_record, _target = migrate(
        args.root,
        args.plan,
        contracts_dir=args.contracts_dir,
        write=not args.dry_run,
    )
    report = {
        "schema_version": "1.0",
        "status": "pass" if not findings else "fail",
        "migration_id": migration_record.get("migration_id") if migration_record else None,
        "dry_run": args.dry_run,
        "findings": [
            {"code": item.code, "location": item.location, "message": item.message}
            for item in findings
        ],
    }
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if findings:
        for finding in findings:
            print(finding.render(), file=sys.stderr)
        return 2
    action = "validated" if args.dry_run else "written"
    print(f"PASS: contract migration {action} without synthesizing scientific evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
