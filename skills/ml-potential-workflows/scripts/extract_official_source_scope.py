#!/usr/bin/env python3
"""Generate the ML provider source seed and extracted scope catalog.

This generator is deliberately offline.  It consumes only reviewed, tracked
metadata beneath ``ml-potential-workflows`` and never retrieves, imports, opens,
or deserializes a provider model, checkpoint, dataset, or documentation body.
The generated source catalogs therefore remain metadata-only and the aggregate
seed remains honestly blocked.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any, Iterable, Sequence

from jsonschema import Draft202012Validator, FormatChecker


DEVELOPMENT_MAINTENANCE_CHECK_IS_OFFLINE = True

SKILL_ID = "ml-potential-workflows"
SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parents[1]
REPOSITORY_ROOT = SCRIPT_PATH.parents[3]
INPUT_PATH = SKILL_ROOT / "references" / "source-pack-inputs.json"
CATALOG_DIRECTORY = SKILL_ROOT / "references"
CATALOG_FILENAME_PREFIX = "source-catalog-"
SCOPE_PATH = SKILL_ROOT / "references" / "source-pack-scope-catalog.json"
SEED_PATH = SKILL_ROOT / "references" / "source-pack-seed.json"
PROPOSAL_PATH = SKILL_ROOT / "references" / "source-pack-authority-proposal.json"

CATALOG_SCHEMA_PATH = (
    REPOSITORY_ROOT / "contracts" / "official-document-source-catalog.schema.json"
)
SCOPE_SCHEMA_PATH = (
    REPOSITORY_ROOT / "contracts" / "official-document-scope-catalog.schema.json"
)
SEED_SCHEMA_PATH = (
    REPOSITORY_ROOT / "contracts" / "official-document-pack-seed.schema.json"
)

CATALOG_FIELDS = frozenset(
    {
        "schema_version",
        "contract_name",
        "version_scope",
        "upstream_universe_complete",
        "inventory_locator",
        "sources",
        "subjects",
        "reviewed_exclusions",
        "losses",
        "license",
        "limitations",
        "blockers",
    }
)
PROVIDER_FIELDS = frozenset(
    {
        "input_id",
        "adapter_id",
        "authority_id",
        "provider_id",
        "provider_class",
        "catalog_filename",
        "storage_policy",
        *CATALOG_FIELDS,
    }
)
CATALOG_SUBJECT_FIELDS = frozenset(
    {
        "subject_id",
        "title",
        "category",
        "requirement_strength",
        "evidence_class",
    }
)
SCOPE_SUBJECT_FIELDS = frozenset(
    {
        "subject_kind",
        "statement",
        "expected_disposition",
    }
)
MODEL_SUFFIXES = (
    ".ckpt",
    ".model",
    ".nequip.zip",
    ".pt",
    ".pt2",
    ".pth",
    ".pkl",
    ".pickle",
)
FORBIDDEN_INCLUDED_LOCATOR_PARTS = (
    "/resolve/",
    "/download/",
    "/checkpoints/",
)


class SourceSeedError(ValueError):
    """Stable fail-closed error for malformed ML source metadata."""


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SourceSeedError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceSeedError(f"{path}: cannot load strict JSON: {exc}") from None
    if not isinstance(value, dict):
        raise SourceSeedError(f"{path}: root must be an object")
    return value


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _schema_validator(path: Path) -> Draft202012Validator:
    schema = load_json(path)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _validate_schema(
    value: dict[str, Any],
    validator: Draft202012Validator,
    label: str,
) -> None:
    errors = sorted(
        validator.iter_errors(value),
        key=lambda item: (
            tuple(str(part) for part in item.absolute_path),
            item.message,
        ),
    )
    if errors:
        rendered = "; ".join(
            f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: "
            f"{error.message}"
            for error in errors
        )
        raise SourceSeedError(f"{label}: schema validation failed: {rendered}")


def _safe_repo_path(value: object) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise SourceSeedError("origin path must be a nonempty POSIX path")
    relative = PurePosixPath(value)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise SourceSeedError(f"unsafe origin path: {value!r}")
    if relative.parts[:2] != ("skills", SKILL_ID):
        raise SourceSeedError(
            f"origin path must remain beneath skills/{SKILL_ID}: {value!r}"
        )
    return relative


def _unique(values: Iterable[str], label: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise SourceSeedError(f"{label}: duplicate identifier {value!r}")
        seen.add(value)


def _catalog_relative(provider: dict[str, Any]) -> str:
    filename = provider.get("catalog_filename")
    if (
        not isinstance(filename, str)
        or not filename.startswith(CATALOG_FILENAME_PREFIX)
        or not filename.endswith(".json")
        or PurePosixPath(filename).name != filename
    ):
        raise SourceSeedError(
            f"{provider.get('input_id', '<provider>')}: catalog_filename must be "
            f"a direct references/{CATALOG_FILENAME_PREFIX}*.json filename"
        )
    return PurePosixPath(
        "skills",
        SKILL_ID,
        "references",
        filename,
    ).as_posix()


def _validate_external_only_provider(provider: dict[str, Any]) -> None:
    storage_policy = provider["storage_policy"]
    if storage_policy not in {"metadata-only", "external-runtime-only"}:
        raise SourceSeedError(
            f"{provider['input_id']}: unsupported D4 storage policy {storage_policy!r}"
        )
    for source in provider["sources"]:
        if "content_ref" in source or "external_identity" not in source:
            raise SourceSeedError(
                f"{provider['input_id']}:{source.get('source_id')}: "
                "D4 included sources must use external_identity only"
            )
        locator = source["locator"].lower()
        if any(part in locator for part in FORBIDDEN_INCLUDED_LOCATOR_PARTS):
            raise SourceSeedError(
                f"{provider['input_id']}:{source['source_id']}: "
                "download/checkpoint locator cannot be an included source"
            )
        if locator.endswith(MODEL_SUFFIXES):
            raise SourceSeedError(
                f"{provider['input_id']}:{source['source_id']}: "
                "serialized model bytes cannot be an included source"
            )
        for item in source["slices"]:
            if "content_ref" in item or "external_receipt" not in item:
                raise SourceSeedError(
                    f"{provider['input_id']}:{source['source_id']}: "
                    "D4 slices must use external_receipt only"
                )
            if item["selector"]["layer"] != "raw-source":
                raise SourceSeedError(
                    f"{provider['input_id']}:{source['source_id']}: "
                    "metadata-only slices must bind raw-source identities"
                )
            if (
                item["selector"]["kind"] == "whole-source"
                and item["selector"]["value"] != "*"
            ):
                raise SourceSeedError(
                    f"{provider['input_id']}:{source['source_id']}: "
                    "whole-source selectors must use the canonical '*' value"
                )
    if provider["provider_class"] == "model-artifact":
        allowed_modes = set(provider["license"]["allowed_storage_modes"])
        if "metadata-only" not in allowed_modes:
            raise SourceSeedError(
                f"{provider['input_id']}: model-artifact metadata must remain "
                "metadata-only"
            )


def _catalog_from_provider(provider: dict[str, Any]) -> dict[str, Any]:
    if set(provider) != PROVIDER_FIELDS:
        missing = sorted(PROVIDER_FIELDS - set(provider))
        extra = sorted(set(provider) - PROVIDER_FIELDS)
        raise SourceSeedError(
            f"{provider.get('input_id', '<provider>')}: provider fields differ; "
            f"missing={missing}, extra={extra}"
        )
    _validate_external_only_provider(provider)
    catalog = {
        key: copy.deepcopy(provider[key])
        for key in sorted(CATALOG_FIELDS)
    }
    catalog_subjects: list[dict[str, Any]] = []
    for subject in provider["subjects"]:
        expected = CATALOG_SUBJECT_FIELDS | SCOPE_SUBJECT_FIELDS
        if set(subject) != expected:
            raise SourceSeedError(
                f"{provider['input_id']}:{subject.get('subject_id')}: "
                "subject fields differ from the D4 extractor contract"
            )
        catalog_subjects.append(
            {key: copy.deepcopy(subject[key]) for key in sorted(CATALOG_SUBJECT_FIELDS)}
        )
    catalog["subjects"] = catalog_subjects
    return catalog


def _proposal_from_input(value: dict[str, Any]) -> dict[str, Any]:
    authorities = copy.deepcopy(value["authority_proposals"])
    _unique(
        (item["authority_id"] for item in authorities),
        "authority proposal",
    )
    for item in authorities:
        required = {
            "authority_id",
            "provider_id",
            "provider_class",
            "proposed_lifecycle",
            "canonical_roots",
            "version_policy",
            "license_policy",
            "storage_policy",
            "consumer_binding",
            "limitations",
        }
        if set(item) != required:
            raise SourceSeedError(
                f"{item.get('authority_id', '<authority>')}: "
                "authority proposal fields differ"
            )
        if item["storage_policy"]["bundle_content"] != "forbidden":
            raise SourceSeedError(
                f"{item['authority_id']}: D4 proposal cannot authorize bundled content"
            )
    return {
        "schema_version": "1.0",
        "contract_name": "ml-source-authority-proposal",
        "skill_id": SKILL_ID,
        "proposal_status": "review-required",
        "authorities": authorities,
        "limitations": copy.deepcopy(value["proposal_limitations"]),
    }


def _origin_ref(
    path_value: object,
    staged_outputs: dict[str, bytes],
) -> dict[str, str]:
    relative = _safe_repo_path(path_value)
    key = relative.as_posix()
    if key in staged_outputs:
        payload = staged_outputs[key]
    else:
        candidate = REPOSITORY_ROOT.joinpath(*relative.parts)
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(SKILL_ROOT.resolve())
        except (OSError, ValueError):
            raise SourceSeedError(f"origin path is absent or escapes Skill: {key}") from None
        if not candidate.is_file() or candidate.is_symlink():
            raise SourceSeedError(f"origin path is not a regular file: {key}")
        payload = candidate.read_bytes()
    return {"path": key, "sha256": sha256_bytes(payload)}


def _scope_from_input(
    value: dict[str, Any],
    providers: list[dict[str, Any]],
    staged_outputs: dict[str, bytes],
) -> dict[str, Any]:
    subjects: list[dict[str, Any]] = []
    for provider in providers:
        catalog_path = _catalog_relative(provider)
        catalog_origin = _origin_ref(catalog_path, staged_outputs)
        for subject in provider["subjects"]:
            subjects.append(
                {
                    "subject_id": subject["subject_id"],
                    "subject_kind": subject["subject_kind"],
                    "evidence_class": "official-provider-required",
                    "origin_refs": [catalog_origin],
                    "statement": subject["statement"],
                    "expected_disposition": subject["expected_disposition"],
                    "provider_input_ids": [provider["input_id"]],
                }
            )
    for subject in value["local_subjects"]:
        required = {
            "subject_id",
            "subject_kind",
            "evidence_class",
            "origin_paths",
            "statement",
            "expected_disposition",
        }
        if set(subject) != required:
            raise SourceSeedError(
                f"{subject.get('subject_id', '<local-subject>')}: "
                "local subject fields differ"
            )
        if subject["evidence_class"] == "official-provider-required":
            raise SourceSeedError(
                f"{subject['subject_id']}: local subject cannot claim provider evidence"
            )
        subjects.append(
            {
                "subject_id": subject["subject_id"],
                "subject_kind": subject["subject_kind"],
                "evidence_class": subject["evidence_class"],
                "origin_refs": [
                    _origin_ref(path, staged_outputs)
                    for path in subject["origin_paths"]
                ],
                "statement": subject["statement"],
                "expected_disposition": subject["expected_disposition"],
                "provider_input_ids": [],
            }
        )
    _unique((item["subject_id"] for item in subjects), "scope catalog")
    return {
        "schema_version": "1.0",
        "contract_name": "official-document-scope-catalog",
        "skill_id": SKILL_ID,
        "extractor_id": "ml-provider-source-scope-v1",
        "subjects": subjects,
    }


def _seed_from_input(
    value: dict[str, Any],
    providers: list[dict[str, Any]],
    staged_outputs: dict[str, bytes],
) -> dict[str, Any]:
    scope_relative = SCOPE_PATH.relative_to(REPOSITORY_ROOT).as_posix()
    provider_entries: list[dict[str, Any]] = []
    for provider in providers:
        catalog_relative = _catalog_relative(provider)
        provider_entries.append(
            {
                "input_id": provider["input_id"],
                "adapter_id": provider["adapter_id"],
                "authority_id": provider["authority_id"],
                "provider_id": provider["provider_id"],
                "source_ref": {
                    "path": catalog_relative,
                    "sha256": sha256_bytes(staged_outputs[catalog_relative]),
                },
            }
        )
    return {
        "schema_version": "1.0",
        "contract_name": "official-document-pack-seed",
        "skill_id": SKILL_ID,
        "status_ceiling": "blocked",
        "scope_extractor_id": "ml-provider-source-scope-v1",
        "scope_catalog_ref": {
            "path": scope_relative,
            "sha256": sha256_bytes(staged_outputs[scope_relative]),
        },
        "providers": provider_entries,
        "limitations": copy.deepcopy(value["seed_limitations"]),
        "blockers": copy.deepcopy(value["seed_blockers"]),
    }


def render_outputs(value: dict[str, Any] | None = None) -> dict[str, bytes]:
    source = copy.deepcopy(value) if value is not None else load_json(INPUT_PATH)
    required_top = {
        "schema_version",
        "contract_name",
        "skill_id",
        "providers",
        "local_subjects",
        "authority_proposals",
        "proposal_limitations",
        "seed_limitations",
        "seed_blockers",
    }
    if set(source) != required_top:
        raise SourceSeedError("source-pack input root fields differ")
    if (
        source["schema_version"] != "1.0"
        or source["contract_name"] != "ml-source-pack-inputs"
        or source["skill_id"] != SKILL_ID
    ):
        raise SourceSeedError("source-pack input identity is invalid")
    providers = source["providers"]
    if not isinstance(providers, list) or not providers:
        raise SourceSeedError("source-pack inputs require providers")
    _unique((item["input_id"] for item in providers), "provider inputs")
    _unique((item["catalog_filename"] for item in providers), "catalog filenames")
    _unique((item["authority_id"] for item in providers), "provider authorities")

    catalog_validator = _schema_validator(CATALOG_SCHEMA_PATH)
    scope_validator = _schema_validator(SCOPE_SCHEMA_PATH)
    seed_validator = _schema_validator(SEED_SCHEMA_PATH)
    outputs: dict[str, bytes] = {}
    for provider in providers:
        catalog = _catalog_from_provider(provider)
        _validate_schema(
            catalog,
            catalog_validator,
            f"{provider['input_id']} source catalog",
        )
        relative = _catalog_relative(provider)
        outputs[relative] = canonical_json_bytes(catalog)

    proposal = _proposal_from_input(source)
    proposal_relative = PROPOSAL_PATH.relative_to(REPOSITORY_ROOT).as_posix()
    outputs[proposal_relative] = canonical_json_bytes(proposal)

    scope = _scope_from_input(source, providers, outputs)
    _validate_schema(scope, scope_validator, "source scope catalog")
    scope_relative = SCOPE_PATH.relative_to(REPOSITORY_ROOT).as_posix()
    outputs[scope_relative] = canonical_json_bytes(scope)

    seed = _seed_from_input(source, providers, outputs)
    _validate_schema(seed, seed_validator, "source pack seed")
    seed_relative = SEED_PATH.relative_to(REPOSITORY_ROOT).as_posix()
    outputs[seed_relative] = canonical_json_bytes(seed)
    return outputs


def write_or_check(*, check: bool) -> tuple[str, ...]:
    outputs = render_outputs()
    changed: list[str] = []
    for relative in sorted(outputs):
        target = REPOSITORY_ROOT.joinpath(*PurePosixPath(relative).parts)
        current = target.read_bytes() if target.is_file() else None
        if current == outputs[relative]:
            continue
        changed.append(relative)
        if not check:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(outputs[relative])
    expected_catalogs = {
        REPOSITORY_ROOT.joinpath(*PurePosixPath(path).parts).resolve()
        for path in outputs
        if f"/references/{CATALOG_FILENAME_PREFIX}" in path
    }
    if CATALOG_DIRECTORY.exists():
        extras = {
            item.resolve()
            for item in CATALOG_DIRECTORY.glob(f"{CATALOG_FILENAME_PREFIX}*.json")
            if item.is_file() and not item.is_symlink()
        } - expected_catalogs
        if extras:
            rendered = ", ".join(
                item.relative_to(REPOSITORY_ROOT).as_posix()
                for item in sorted(extras)
            )
            raise SourceSeedError(
                "unregistered generated source catalogs require review: " + rendered
            )
    if check and changed:
        raise SourceSeedError(
            "generated ML source records are stale: " + ", ".join(changed)
        )
    return tuple(changed)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare canonical generated bytes without writing",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        changed = write_or_check(check=args.check)
    except SourceSeedError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    verb = "checked" if args.check else "generated"
    print(f"PASS: {verb} ML official-source seed ({len(changed)} changed paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
