#!/usr/bin/env python3
"""Render the Skill-local metadata-only official-source pack seed."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
INPUT_PATH = SKILL_ROOT / "references" / "source-pack-inputs.json"


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


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


def scope_origin_ref(relative: str, generated: dict[Path, bytes]) -> dict:
    pure = PurePosixPath(relative)
    expected_prefix = PurePosixPath("skills", SKILL_ROOT.name)
    if pure.parts[: len(expected_prefix.parts)] != expected_prefix.parts:
        raise ValueError(
            f"scope origin must remain below {expected_prefix.as_posix()}: "
            f"{relative!r}"
        )
    path = repository_file(relative)
    try:
        path.resolve().relative_to(SKILL_ROOT.resolve())
    except ValueError:
        raise ValueError(
            f"scope origin escapes {expected_prefix.as_posix()}: {relative!r}"
        ) from None
    raw = generated.get(path)
    if raw is None:
        raw = path.read_bytes()
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

    outputs: dict[Path, bytes] = {}
    provider_records: list[dict] = []
    for provider in inputs["providers"]:
        catalog = copy.deepcopy(provider["catalog"])
        catalog["sources"] = [
            materialize_receipt(source) for source in catalog["sources"]
        ]
        if "content_ref" in json.dumps(catalog, sort_keys=True):
            raise ValueError("metadata-only catalogs cannot contain content_ref")
        catalog_path = SKILL_ROOT / "references" / provider["catalog_file"]
        catalog_raw = canonical_bytes(catalog)
        outputs[catalog_path] = catalog_raw
        provider_records.append(
            {
                "input_id": provider["input_id"],
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
        subject["origin_refs"] = [
            scope_origin_ref(path, outputs) for path in origin_paths
        ]
        subjects.append(subject)
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
