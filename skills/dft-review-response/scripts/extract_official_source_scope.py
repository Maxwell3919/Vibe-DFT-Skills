#!/usr/bin/env python3
"""Render the Skill-local metadata-only official-source pack seed."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
from typing import NamedTuple


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
INPUT_PATH = SKILL_ROOT / "references" / "source-pack-inputs.json"
TOOLS = str(REPOSITORY_ROOT / "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

from migrate_official_document_catalogs_v11 import (  # noqa: E402
    CATALOG_WIDE_TECHNICAL_BINDINGS,
    canonical_json_bytes as canonical_bytes,
    convert_catalog_v10_to_v11,
)


class MigrationProjection(NamedTuple):
    authority_root: str
    inventory_source_id: str
    exact_version: str


MIGRATION_PROJECTIONS = {
    "repository-contracts-review-response": MigrationProjection(
        authority_root=(
            "https://raw.githubusercontent.com/Maxwell3919/Vibe-DFT-Skills/"
            "24dd8a9b7fd2758a7c44b82ee7dbb386693b2315/"
            "skills/dft-review-response/references/"
        ),
        inventory_source_id="review-response-repository-source-index",
        exact_version="24dd8a9b7fd2758a7c44b82ee7dbb386693b2315",
    )
}


def load_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def repository_file(relative: str) -> Path:
    pure = PurePosixPath(relative)
    if (
        pure.is_absolute()
        or pure.as_posix() != relative
        or any(part in {"", ".", ".."} for part in pure.parts)
    ):
        raise ValueError(f"unsafe repository-relative path: {relative!r}")
    path = REPOSITORY_ROOT.joinpath(*pure.parts)
    path.resolve().relative_to(REPOSITORY_ROOT.resolve())
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"missing or aliased source path: {relative}")
    return path


def file_ref(relative: str) -> dict:
    raw = repository_file(relative).read_bytes()
    return {"path": relative, "sha256": hashlib.sha256(raw).hexdigest()}


def materialize_receipt(source: dict) -> dict:
    result = copy.deepcopy(source)
    receipt = result.pop("receipt")
    if "path" in receipt:
        raw = repository_file(receipt["path"]).read_bytes()
        raw_sha256 = hashlib.sha256(raw).hexdigest()
        raw_bytes = len(raw)
    else:
        raw_sha256 = receipt["raw_sha256"]
        raw_bytes = receipt["raw_bytes"]
    result["external_identity"] = {
        "kind": receipt["kind"],
        "value": receipt["value"],
        "raw_sha256": raw_sha256,
        "raw_bytes": raw_bytes,
        "retrieved_utc": receipt["retrieved_utc"],
    }
    external_receipt = {
        "retrieval_method": receipt["retrieval_method"],
        "retrieved_utc": receipt["retrieved_utc"],
        "raw_sha256": raw_sha256,
        "raw_bytes": raw_bytes,
        "selected_sha256": raw_sha256,
        "selected_bytes": raw_bytes,
    }
    for slice_record in result["slices"]:
        slice_record["external_receipt"] = copy.deepcopy(external_receipt)
    return result


def render_outputs() -> dict[Path, bytes]:
    inputs = load_object(INPUT_PATH)
    skill_id = SKILL_ROOT.name
    if inputs.get("schema_version") != "1.0" or inputs.get("skill_id") != skill_id:
        raise ValueError("source-pack-inputs.json is not bound to this Skill")
    provider_ids = {provider["input_id"] for provider in inputs["providers"]}
    if provider_ids != set(MIGRATION_PROJECTIONS):
        raise ValueError("provider migration projection ledger is incomplete")

    outputs: dict[Path, bytes] = {}
    provider_records: list[dict] = []
    catalog_paths: dict[str, Path] = {}

    conversion_subjects = []
    for source_subject in inputs["scope_subjects"]:
        subject = copy.deepcopy(source_subject)
        subject.pop("origin_paths")
        subject["origin_refs"] = []
        conversion_subjects.append(subject)
    conversion_scope = {
        "schema_version": "1.0",
        "contract_name": "official-document-scope-catalog",
        "skill_id": skill_id,
        "extractor_id": "repository-native-source-scope-v1",
        "subjects": conversion_subjects,
    }

    for provider in inputs["providers"]:
        legacy_catalog = copy.deepcopy(provider["catalog"])
        legacy_catalog["sources"] = [
            materialize_receipt(source) for source in legacy_catalog["sources"]
        ]
        if "content_ref" in json.dumps(legacy_catalog, sort_keys=True):
            raise ValueError("metadata-only catalogs cannot contain content_ref")

        input_id = provider["input_id"]
        projection = MIGRATION_PROJECTIONS[input_id]
        if legacy_catalog["version_scope"].get("value") != projection.exact_version:
            raise ValueError(f"{input_id}: exact version projection drift")
        included_sources = {
            source["source_id"]: source
            for source in legacy_catalog["sources"]
            if source.get("disposition") == "included"
        }
        inventory_source = included_sources.get(projection.inventory_source_id)
        if inventory_source is None:
            raise ValueError(f"{input_id}: inventory source is missing")
        preimage = canonical_bytes(legacy_catalog)
        catalog = convert_catalog_v10_to_v11(
            legacy_catalog,
            provider=provider,
            authority={"authority_id": provider["authority_id"]},
            authority_projection={
                "canonical_urls": [projection.authority_root],
                "version_scopes": [
                    {
                        "scope": "exact",
                        "exact_version": projection.exact_version,
                    }
                ],
            },
            scope_catalog=conversion_scope,
            inventory_projection={
                "locator": inventory_source["locator"],
                "identity": {
                    "sha256": hashlib.sha256(preimage).hexdigest(),
                    "bytes": len(preimage),
                },
                "canonical_preimage_bytes": preimage,
            },
        )
        catalog_path = SKILL_ROOT / "references" / provider["catalog_file"]
        catalog_raw = canonical_bytes(catalog)
        outputs[catalog_path] = catalog_raw
        catalog_paths[input_id] = catalog_path
        provider_records.append(
            {
                "input_id": input_id,
                "adapter_id": "declarative-catalog-v1",
                "authority_id": provider["authority_id"],
                "provider_id": provider["provider_id"],
                "source_ref": {
                    "path": catalog_path.relative_to(REPOSITORY_ROOT).as_posix(),
                    "sha256": hashlib.sha256(catalog_raw).hexdigest(),
                },
            }
        )

    subjects = []
    for source_subject in inputs["scope_subjects"]:
        subject = copy.deepcopy(source_subject)
        origin_paths = subject.pop("origin_paths")
        subject["origin_refs"] = [file_ref(path) for path in origin_paths]
        subjects.append(subject)
    for provider in inputs["providers"]:
        input_id = provider["input_id"]
        binding = CATALOG_WIDE_TECHNICAL_BINDINGS.get(input_id)
        if binding is None:
            continue
        catalog_path = catalog_paths[input_id]
        subjects.append(
            {
                "subject_id": binding["subject_id"],
                "subject_kind": "documented-claim",
                "evidence_class": "official-provider-required",
                "origin_refs": [
                    {
                        "path": catalog_path.relative_to(
                            REPOSITORY_ROOT
                        ).as_posix(),
                        "sha256": hashlib.sha256(
                            outputs[catalog_path]
                        ).hexdigest(),
                    }
                ],
                "statement": binding["statement"],
                "expected_disposition": "partial",
                "provider_input_ids": [input_id],
            }
        )
    scope = {
        "schema_version": "1.0",
        "contract_name": "official-document-scope-catalog",
        "skill_id": skill_id,
        "extractor_id": "repository-native-source-scope-v1",
        "subjects": subjects,
    }
    scope_path = SKILL_ROOT / "references" / "source-pack-scope-catalog.json"
    scope_raw = canonical_bytes(scope)
    outputs[scope_path] = scope_raw

    seed = {
        "schema_version": "1.0",
        "contract_name": "official-document-pack-seed",
        "skill_id": skill_id,
        "status_ceiling": inputs["seed"]["status_ceiling"],
        "scope_extractor_id": "repository-native-source-scope-v1",
        "scope_catalog_ref": {
            "path": scope_path.relative_to(REPOSITORY_ROOT).as_posix(),
            "sha256": hashlib.sha256(scope_raw).hexdigest(),
        },
        "providers": provider_records,
        "limitations": inputs["seed"]["limitations"],
        "blockers": inputs["seed"]["blockers"],
    }
    outputs[SKILL_ROOT / "references" / "source-pack-seed.json"] = canonical_bytes(
        seed
    )
    outputs[
        SKILL_ROOT / "references" / "source-pack-authority-proposal.json"
    ] = canonical_bytes(inputs["authority_proposal"])
    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    stale = []
    for path, expected in render_outputs().items():
        if args.check:
            if not path.is_file() or path.read_bytes() != expected:
                stale.append(path.relative_to(REPOSITORY_ROOT).as_posix())
        else:
            path.write_bytes(expected)
    if stale:
        for path in stale:
            print(f"STALE: {path}", file=sys.stderr)
        return 1
    print(f"PASS: {SKILL_ROOT.name} source-pack metadata is current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
