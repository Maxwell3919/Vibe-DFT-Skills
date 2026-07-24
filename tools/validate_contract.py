#!/usr/bin/env python3
"""Validate JSON instances against the local Vibe-DFT contract catalog."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import hashlib
from pathlib import Path
import re
import sys
from typing import Any, Iterator

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource, Unresolvable, Unretrievable
from referencing.jsonschema import DRAFT202012

import strict_json
from registry_yaml import RegistryYAMLError, load_yaml_strict


DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"
CANONICAL_ID_PATTERN = re.compile(
    r"^urn:vibe-dft-skills:contract:"
    r"(?P<name>[a-z][a-z0-9]*(?:-[a-z0-9]+)*):"
    r"(?P<version>(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*))$"
)
RFC3339_DATE_TIME_PATTERN = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt]"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?"
    r"(?:[Zz]|[+-][0-9]{2}:[0-9]{2})$"
)
FORMAT_CHECKER = FormatChecker()
SCHEMA_MAX_BYTES = 8 * 1024 * 1024


@FORMAT_CHECKER.checks("date-time", raises=(TypeError, ValueError))
def _is_rfc3339_date_time(value: object) -> bool:
    """Supply the optional RFC 3339 checker when jsonschema extras are absent."""

    if not isinstance(value, str):
        return True
    if RFC3339_DATE_TIME_PATTERN.fullmatch(value) is None:
        return False
    normalized = value.replace("t", "T").replace("z", "Z")
    # datetime does not accept RFC 3339's leap-second spelling.  Substituting
    # 59 here retains calendar/offset validation without rejecting second 60.
    date_part, time_part = normalized.split("T", 1)
    if time_part[6:8] == "60":
        if time_part[:5] != "23:59":
            return False
        normalized = f"{date_part}T{time_part[:6]}59{time_part[8:]}"
    datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    return True


# Public compatibility surface used by existing callers and tests.  Catalog
# discovery is dynamic; this mapping only preserves the original short CLI
# selectors and their exact v1 targets.
SCHEMAS = {
    "run": "run-manifest.schema.json",
    "artifact": "artifact-manifest.schema.json",
    "campaign": "campaign-record.schema.json",
    "recommendation": "recommendation-record.schema.json",
    "dataset": "normalized-dataset.schema.json",
    "plan": "postprocess-plan.schema.json",
    "execution": "tool-execution.schema.json",
    "structure": "structure-manifest.schema.json",
}

# These eight published v1 schemas predate the canonical URN convention.  The
# exception is intentionally bound to both an exact filename and an exact ID;
# no other HTTP(S) schema ID is accepted.
LEGACY_SCHEMA_IDS = {
    filename: f"https://example.invalid/vibe-dft-skills/{filename}"
    for filename in SCHEMAS.values()
}
LEGACY_RECORD_ID_FIELDS = {
    "run-manifest.schema.json": "record_id",
    "artifact-manifest.schema.json": "artifact_id",
    "campaign-record.schema.json": "record_id",
    "recommendation-record.schema.json": "recommendation_id",
    "normalized-dataset.schema.json": "dataset_id",
    "postprocess-plan.schema.json": "plan_id",
    "tool-execution.schema.json": "execution_id",
    "structure-manifest.schema.json": "manifest_id",
}
DOCUMENT_KINDS = frozenset(
    {"content-addressed-record", "projection", "definition-library"}
)
SAFE_ID_PATTERNS = frozenset(
    {
        r"^[a-z0-9][a-z0-9._-]{2,127}$",
        r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$",
    }
)
SINGLE_SUBSCHEMA_KEYWORDS = (
    "additionalProperties",
    "contains",
    "contentSchema",
    "else",
    "if",
    "items",
    "not",
    "propertyNames",
    "then",
    "unevaluatedItems",
    "unevaluatedProperties",
)
ARRAY_SUBSCHEMA_KEYWORDS = ("allOf", "anyOf", "oneOf", "prefixItems")
MAPPING_SUBSCHEMA_KEYWORDS = (
    "$defs",
    "dependentSchemas",
    "patternProperties",
    "properties",
)


class CatalogError(ValueError):
    """The local schema catalog is incomplete, ambiguous, or invalid."""

    def __init__(self, errors: list[str] | tuple[str, ...]) -> None:
        self.errors = tuple(errors)
        super().__init__("\n".join(self.errors))


class ContractSelectionError(LookupError):
    """A requested contract selector cannot be resolved unambiguously."""


@dataclass(frozen=True)
class ContractSchema:
    path: Path
    filename: str
    raw_bytes: bytes
    raw_sha256: str
    name: str
    version: str
    schema_id: str
    canonical_id: str
    catalog_kind: str
    document_kind: str
    record_id_field: str | None
    is_legacy: bool
    schema: dict[str, Any]

    @property
    def is_record_ref_target(self) -> bool:
        """Whether this contract has content-addressed record identity semantics."""

        return self.document_kind == "content-addressed-record"


@dataclass
class ContractCatalog:
    contracts: tuple[ContractSchema, ...]
    registry: Registry
    by_filename: dict[str, ContractSchema]
    by_schema_id: dict[str, ContractSchema]
    by_canonical_id: dict[str, ContractSchema]
    by_name: dict[str, tuple[ContractSchema, ...]]

    def resolve(self, selector: str) -> ContractSchema:
        """Resolve a legacy alias, canonical name, version selector, or ID."""

        legacy_filename = SCHEMAS.get(selector)
        if legacy_filename is not None:
            contract = self.by_filename.get(legacy_filename)
            if contract is not None:
                return contract

        direct = self.by_canonical_id.get(selector) or self.by_schema_id.get(selector)
        if direct is not None:
            return direct

        if "@" in selector:
            name, version = selector.rsplit("@", 1)
            canonical_id = canonical_contract_id(name, version)
            versioned = self.by_canonical_id.get(canonical_id)
            if versioned is not None:
                return versioned

        candidates = self.by_name.get(selector, ())
        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) > 1:
            choices = ", ".join(
                f"{selector}@{contract.version}" for contract in candidates
            )
            raise ContractSelectionError(
                f"ambiguous contract kind '{selector}'; choose one of: "
                f"{choices}"
            )
        raise ContractSelectionError(f"unknown contract kind '{selector}'")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def canonical_contract_id(name: str, version: str) -> str:
    return f"urn:vibe-dft-skills:contract:{name}:{version}"


def _offline_retrieve(uri: str) -> Resource[Any]:
    """Fail closed instead of retrieving a schema over the network."""

    raise NoSuchResource(ref=uri)


def _schema_basename(filename: str) -> str:
    suffix = ".schema.json"
    if not filename.endswith(suffix):
        return filename
    return filename[: -len(suffix)]


def _parse_contract_identity(
    path: Path,
    schema_id: object,
) -> tuple[str, str, str, bool] | None:
    """Return name, version, canonical ID, and legacy state for an accepted ID."""

    if not isinstance(schema_id, str):
        return None

    match = CANONICAL_ID_PATTERN.fullmatch(schema_id)
    if match is not None:
        name = match.group("name")
        version = match.group("version")
        basename = _schema_basename(path.name)
        if basename not in (name, f"{name}-{version}"):
            return None
        return name, version, schema_id, False

    if LEGACY_SCHEMA_IDS.get(path.name) == schema_id:
        name = _schema_basename(path.name)
        version = "1.0"
        return name, version, canonical_contract_id(name, version), True
    return None


def _safe_id_schema(root_schema: dict[str, Any], candidate: object) -> bool:
    """Recognize the catalog's intentionally narrow safe-ID schema forms."""

    if not isinstance(candidate, dict):
        return False
    reference = candidate.get("$ref")
    if reference == "#/$defs/safeId":
        definitions = root_schema.get("$defs")
        if not isinstance(definitions, dict):
            return False
        candidate = definitions.get("safeId")
    elif reference == (
        "urn:vibe-dft-skills:contract:common-definitions:1.0#/$defs/safeId"
    ):
        # The referenced definition is itself cataloged and reference-closed.
        return True
    if not isinstance(candidate, dict):
        return False
    return (
        candidate.get("type") == "string"
        and candidate.get("pattern") in SAFE_ID_PATTERNS
    )


def _catalog_kind_and_identity_errors(
    path: Path,
    schema: dict[str, Any],
    name: str,
    version: str,
    is_legacy: bool,
) -> tuple[str, str, str | None, list[str]]:
    if is_legacy:
        return (
            "instance-contract",
            "content-addressed-record",
            LEGACY_RECORD_ID_FIELDS[path.name],
            [],
        )

    errors = []
    document_kind = schema.get("x-vibe-document-kind")
    if document_kind not in DOCUMENT_KINDS:
        errors.append(
            f"{path.name}: x-vibe-document-kind must be exactly one of: "
            f"{', '.join(sorted(DOCUMENT_KINDS))}"
        )
        document_kind = "invalid"

    record_id_field = schema.get("x-vibe-record-id-field")
    if document_kind == "definition-library":
        if record_id_field is not None:
            errors.append(
                f"{path.name}: definition-library must not declare "
                "x-vibe-record-id-field"
            )
        definitions = schema.get("$defs")
        if not isinstance(definitions, dict) or not definitions:
            errors.append(
                f"{path.name}: definition-library must contain a non-empty $defs object"
            )
        elif name == "common-definitions" and not _safe_id_schema(
            schema, definitions.get("safeId")
        ):
            errors.append(
                f"{path.name}: common-definitions $defs.safeId must be a string "
                "safe-ID schema"
            )
        payload_keywords = sorted(
            keyword for keyword in ("type", "properties", "required") if keyword in schema
        )
        if payload_keywords:
            errors.append(
                f"{path.name}: definition-library must not declare instance payload "
                f"keywords: {', '.join(payload_keywords)}"
            )
        return "definition-library", document_kind, None, errors

    if schema.get("type") != "object":
        errors.append(
            f"{path.name}: self-description requires a top-level object schema"
        )

    properties = schema.get("properties")
    required = schema.get("required")
    if not isinstance(properties, dict):
        errors.append(
            f"{path.name}: self-description requires a top-level properties object"
        )
        properties = {}
    if not isinstance(required, list):
        errors.append(
            f"{path.name}: self-description requires a top-level required array"
        )
        required = []

    expected = {"contract_name": name, "schema_version": version}
    for field, value in expected.items():
        field_schema = properties.get(field)
        if not isinstance(field_schema, dict) or field_schema.get("const") != value:
            errors.append(
                f"{path.name}: self-description properties.{field}.const must be "
                f"'{value}' to match $id"
            )
        if field not in required:
            errors.append(
                f"{path.name}: self-description must require '{field}'"
            )

    if document_kind == "projection":
        if record_id_field is not None:
            errors.append(
                f"{path.name}: projection must not declare x-vibe-record-id-field"
            )
        record_id_field = None
    elif document_kind == "content-addressed-record":
        if not isinstance(record_id_field, str) or not record_id_field:
            errors.append(
                f"{path.name}: content-addressed-record requires a non-empty "
                "x-vibe-record-id-field"
            )
            record_id_field = None
        else:
            if record_id_field not in required:
                errors.append(
                    f"{path.name}: record ID field '{record_id_field}' must be "
                    "top-level required"
                )
            field_schema = properties.get(record_id_field)
            if not _safe_id_schema(schema, field_schema):
                errors.append(
                    f"{path.name}: record ID field '{record_id_field}' must be a "
                    "top-level string safe-ID schema"
                )
    elif record_id_field is not None:
        errors.append(
            f"{path.name}: invalid document kind must not declare "
            "x-vibe-record-id-field"
        )

    return "instance-contract", document_kind, record_id_field, errors


def _json_pointer(parts: tuple[object, ...]) -> str:
    if not parts:
        return "<root>"
    encoded = []
    for part in parts:
        encoded.append(str(part).replace("~", "~0").replace("/", "~1"))
    return "/" + "/".join(encoded)


def _iter_schema_references(
    node: object,
    resolver: Any,
    path: tuple[object, ...] = (),
    *,
    root: bool = True,
) -> Iterator[tuple[str, str, tuple[object, ...], Any]]:
    """Yield only references which occur in actual Draft 2020-12 schemas."""

    if not isinstance(node, dict):
        return

    current_resolver = resolver
    if not root and "$id" in node:
        subresource = Resource.from_contents(
            node,
            default_specification=DRAFT202012,
        )
        current_resolver = resolver.in_subresource(subresource)

    for keyword in ("$ref", "$dynamicRef"):
        reference = node.get(keyword)
        if isinstance(reference, str):
            yield keyword, reference, (*path, keyword), current_resolver

    for keyword in SINGLE_SUBSCHEMA_KEYWORDS:
        child = node.get(keyword)
        if isinstance(child, (dict, bool)):
            yield from _iter_schema_references(
                child,
                current_resolver,
                (*path, keyword),
                root=False,
            )

    for keyword in ARRAY_SUBSCHEMA_KEYWORDS:
        children = node.get(keyword)
        if isinstance(children, list):
            for index, child in enumerate(children):
                if isinstance(child, (dict, bool)):
                    yield from _iter_schema_references(
                        child,
                        current_resolver,
                        (*path, keyword, index),
                        root=False,
                    )

    for keyword in MAPPING_SUBSCHEMA_KEYWORDS:
        children = node.get(keyword)
        if isinstance(children, dict):
            for label, child in children.items():
                if isinstance(child, (dict, bool)):
                    yield from _iter_schema_references(
                        child,
                        current_resolver,
                        (*path, keyword, label),
                        root=False,
                    )


def _deduplicate(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def load_catalog(contracts_dir: Path | None = None) -> ContractCatalog:
    """Load, meta-validate, index, and close all local schema references."""

    directory = Path(contracts_dir) if contracts_dir is not None else repo_root() / "contracts"
    if not directory.is_dir():
        raise CatalogError([f"catalog directory does not exist: {directory}"])

    try:
        paths = sorted(directory.glob("*.schema.json"), key=lambda item: item.name)
    except OSError as exc:
        raise CatalogError([f"cannot list catalog directory '{directory}': {exc}"]) from exc
    if not paths:
        raise CatalogError([f"catalog contains no *.schema.json files: {directory}"])

    errors: list[str] = []
    contracts: list[ContractSchema] = []
    seen_schema_ids: dict[str, str] = {}
    seen_canonical_ids: dict[str, str] = {}

    for path in paths:
        try:
            raw = strict_json.read_bytes_bounded(
                path,
                path.name,
                max_bytes=SCHEMA_MAX_BYTES,
            )
            schema = strict_json.loads_object(
                raw,
                path.name,
                max_bytes=SCHEMA_MAX_BYTES,
            )
        except (OSError, strict_json.StrictJSONError) as exc:
            errors.append(
                f"{path.name}: STRICT_JSON_INVALID schema '{path.name}': {exc}"
            )
            continue

        if not isinstance(schema, dict):
            errors.append(f"{path.name}: schema root must be a JSON object")
            continue

        if schema.get("$schema") != DRAFT_2020_12:
            errors.append(
                f"{path.name}: $schema must declare Draft 2020-12 "
                f"('{DRAFT_2020_12}')"
            )
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            errors.append(f"{path.name}: Draft 2020-12 meta-validation failed: {exc.message}")

        schema_id = schema.get("$id")
        if isinstance(schema_id, str):
            previous = seen_schema_ids.get(schema_id)
            if previous is not None:
                errors.append(
                    f"{path.name}: duplicate $id '{schema_id}' also declared by {previous}"
                )
            else:
                seen_schema_ids[schema_id] = path.name

        identity = _parse_contract_identity(path, schema_id)
        if identity is None:
            errors.append(
                f"{path.name}: $id must be a canonical URN matching "
                "'urn:vibe-dft-skills:contract:<name>:<major.minor>' and the "
                "filename; only the exact eight legacy filename/ID pairs are allowed"
            )
            continue

        name, version, canonical_id, is_legacy = identity
        (
            catalog_kind,
            document_kind,
            record_id_field,
            identity_errors,
        ) = _catalog_kind_and_identity_errors(
            path,
            schema,
            name,
            version,
            is_legacy,
        )
        errors.extend(identity_errors)
        previous_canonical = seen_canonical_ids.get(canonical_id)
        if previous_canonical is not None:
            errors.append(
                f"{path.name}: duplicate canonical contract ID '{canonical_id}' "
                f"also declared by {previous_canonical}"
            )
        else:
            seen_canonical_ids[canonical_id] = path.name

        contracts.append(
            ContractSchema(
                path=path,
                filename=path.name,
                raw_bytes=raw,
                raw_sha256=hashlib.sha256(raw).hexdigest(),
                name=name,
                version=version,
                schema_id=str(schema_id),
                canonical_id=canonical_id,
                catalog_kind=catalog_kind,
                document_kind=document_kind,
                record_id_field=record_id_field,
                is_legacy=is_legacy,
                schema=schema,
            )
        )

    if errors:
        raise CatalogError(_deduplicate(errors))

    registry: Registry = Registry(retrieve=_offline_retrieve)
    resources: dict[str, Resource[Any]] = {}
    for contract in contracts:
        resource = Resource.from_contents(contract.schema)
        resources[contract.schema_id] = resource
        # A canonical local alias lets new schemas reference an unchanged legacy
        # v1 contract without making its published $id disappear.
        resources[contract.canonical_id] = resource
    registry = registry.with_resources(resources.items()).crawl()

    reference_errors: list[str] = []
    for contract in contracts:
        resolver = registry.resolver(base_uri=contract.schema_id)
        for _keyword, reference, path, reference_resolver in _iter_schema_references(
            contract.schema,
            resolver,
        ):
            try:
                reference_resolver.lookup(reference)
            except (Unresolvable, NoSuchResource, Unretrievable) as exc:
                reference_errors.append(
                    f"{contract.filename}{_json_pointer(path)}: unresolved reference "
                    f"'{reference}' ({exc})"
                )
    if reference_errors:
        raise CatalogError(_deduplicate(reference_errors))

    ordered = tuple(sorted(contracts, key=lambda item: item.filename))
    by_filename = {contract.filename: contract for contract in ordered}
    by_schema_id = {contract.schema_id: contract for contract in ordered}
    by_canonical_id = {contract.canonical_id: contract for contract in ordered}
    names: dict[str, list[ContractSchema]] = {}
    for contract in ordered:
        names.setdefault(contract.name, []).append(contract)
    by_name = {
        name: tuple(
            sorted(
                candidates,
                key=lambda item: tuple(int(part) for part in item.version.split(".")),
            )
        )
        for name, candidates in names.items()
    }
    return ContractCatalog(
        contracts=ordered,
        registry=registry,
        by_filename=by_filename,
        by_schema_id=by_schema_id,
        by_canonical_id=by_canonical_id,
        by_name=by_name,
    )


def load_schema(kind: str, contracts_dir: Path | None = None) -> dict[str, Any]:
    """Load a schema by legacy alias or canonical contract selector."""

    return load_catalog(contracts_dir).resolve(kind).schema


def validation_errors(
    kind: str,
    data: object,
    contracts_dir: Path | None = None,
) -> list[str]:
    try:
        catalog = load_catalog(contracts_dir)
    except CatalogError as exc:
        return [f"<catalog>: {error}" for error in exc.errors]

    try:
        contract = catalog.resolve(kind)
    except ContractSelectionError as exc:
        return [f"<selector>: {exc}"]
    if contract.catalog_kind != "instance-contract":
        return [
            f"<selector>: contract '{contract.name}' is a {contract.catalog_kind}, "
            "not an instance-validation contract"
        ]

    validator = Draft202012Validator(
        contract.schema,
        registry=catalog.registry,
        format_checker=FORMAT_CHECKER,
    )
    try:
        discovered = list(validator.iter_errors(data))
    except Exception as exc:  # Fail closed for late dynamic-reference failures.
        return [f"<schema>: validation could not resolve locally: {exc}"]

    errors = []
    for error in sorted(
        discovered,
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    ):
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        errors.append(f"{location}: {error.message}")
    return errors


def validate_file(
    kind: str,
    path: Path,
    contracts_dir: Path | None = None,
) -> list[str]:
    try:
        data = strict_json.load_object(path, path.name)
    except (OSError, strict_json.StrictJSONError) as exc:
        return [
            f"<file>: STRICT_JSON_INVALID instance '{path.name}': {exc}"
        ]
    return validation_errors(kind, data, contracts_dir)


def runtime_interface_lifecycle(
    contract: ContractSchema,
    catalog: ContractCatalog,
    registry_file: Path | None = None,
    repository_root: Path | None = None,
) -> str:
    """Resolve the fixed runtime lifecycle and cross-bind an active schema hash."""

    selected = registry_file or repo_root() / "registry" / "interface-registry.yaml"
    try:
        registry = load_yaml_strict(selected)
    except RegistryYAMLError as exc:
        raise CatalogError([f"runtime interface registry is unreadable: {exc}"]) from exc
    if set(registry) != {"schema_version", "interfaces"}:
        raise CatalogError(["runtime interface registry has unexpected top-level fields"])
    if registry.get("schema_version") != "1.0":
        raise CatalogError(["runtime interface registry schema_version must be '1.0'"])
    interfaces = registry.get("interfaces")
    if not isinstance(interfaces, dict):
        raise CatalogError(["runtime interface registry interfaces must be a mapping"])
    interface_id = f"{contract.name}@{contract.version}"
    entry = interfaces.get(interface_id)
    if entry is None:
        return "unregistered"
    if not isinstance(entry, dict):
        raise CatalogError([f"runtime interface '{interface_id}' must be a mapping"])
    lifecycle = entry.get("lifecycle")
    if lifecycle == "planned":
        if entry.get("schema_path") is not None or entry.get("schema_sha256") is not None:
            raise CatalogError(
                [f"planned runtime interface '{interface_id}' must not bind a schema"]
            )
        return "planned"
    if lifecycle != "active":
        raise CatalogError([f"runtime interface '{interface_id}' has invalid lifecycle"])
    expected_relative = f"contracts/{contract.filename}"
    if entry.get("schema_path") != expected_relative:
        raise CatalogError(
            [f"active runtime interface '{interface_id}' does not bind the catalog schema path"]
        )
    declared_hash = entry.get("schema_sha256")
    if declared_hash != contract.raw_sha256:
        raise CatalogError(
            [f"active runtime interface '{interface_id}' schema hash does not match catalog bytes"]
        )
    canonical_path = (repository_root or repo_root()) / expected_relative
    if contract.path.resolve() != canonical_path.resolve():
        raise CatalogError(
            [f"active runtime interface '{interface_id}' is not from the canonical catalog"]
        )
    # Defend against a catalog object assembled from different bytes at the same
    # selector, even though normal callers use load_catalog directly.
    indexed = catalog.by_filename.get(contract.filename)
    if indexed is not contract and (
        indexed is None or indexed.schema_id != contract.schema_id
    ):
        raise CatalogError([f"runtime interface '{interface_id}' catalog identity is ambiguous"])
    return "active"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contracts-dir",
        type=Path,
        default=repo_root() / "contracts",
        help="local directory containing *.schema.json (default: repository contracts/)",
    )
    parser.add_argument(
        "--allow-draft",
        action="store_true",
        help=(
            "maintenance-only schema validation for planned, unregistered, or "
            "noncanonical catalogs; always exits 3 on schema success"
        ),
    )
    parser.add_argument(
        "kind",
        help="legacy alias, canonical contract name, name@version, or canonical URN",
    )
    parser.add_argument("json_file", type=Path)
    args = parser.parse_args()

    canonical_catalog = (repo_root() / "contracts").resolve()
    selected_catalog = args.contracts_dir.resolve()
    if selected_catalog != canonical_catalog and not args.allow_draft:
        print(
            "<runtime-policy>: noncanonical --contracts-dir requires --allow-draft "
            "and can never produce active assurance",
            file=sys.stderr,
        )
        return 2

    try:
        catalog = load_catalog(args.contracts_dir)
        contract = catalog.resolve(args.kind)
        lifecycle = (
            runtime_interface_lifecycle(contract, catalog)
            if selected_catalog == canonical_catalog
            else "maintenance"
        )
    except (CatalogError, ContractSelectionError) as exc:
        print(f"<catalog>: {exc}", file=sys.stderr)
        return 2

    if lifecycle != "active" and not args.allow_draft:
        print(
            f"BLOCKED: {contract.name}@{contract.version} lifecycle={lifecycle}; "
            "use --allow-draft only for maintenance schema checks "
            "(assurance=contract-only/no_positive_claim)",
            file=sys.stderr,
        )
        return 3

    errors = validate_file(args.kind, args.json_file, args.contracts_dir)
    if errors:
        for item in errors:
            print(item, file=sys.stderr)
        return 2

    if lifecycle != "active":
        print(
            f"BLOCKED: {args.json_file.name} matches {contract.name}@{contract.version} "
            f"for maintenance only (lifecycle={lifecycle}; "
            "assurance=contract-only/no_positive_claim)"
        )
        return 3
    print(
        f"PASS: {args.json_file.name} matches "
        f"active {contract.name}@{contract.version} ({contract.filename}); "
        "assurance=contract-structure-only/no_positive_claim"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
