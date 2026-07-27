#!/usr/bin/env python3
"""Plan, verify, and atomically apply the official-document v1.1 input migration."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile
from typing import Any
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker

from migrate_official_document_catalogs_v11 import (
    CATALOG_WIDE_TECHNICAL_BINDINGS,
    LEGACY_RECORD_ACTIONS,
    MigrationError,
    canonical_projection_bytes,
    canonical_json_bytes,
    convert_catalog_v10_to_v11,
)
from official_source_authorities import cp2k_source_id, validate_and_project
from registry_yaml import load_yaml_strict


EXPECTED_SEEDS = 26
EXPECTED_DECLARATIVE_CATALOGS = 55
EXPECTED_SCOPE_CATALOGS = 26
EXPECTED_LEGACY_SEED_ACTIONS = 21

SEED_TEXT_ACTIONS: tuple[tuple[str, str, str, str], ...] = (
    (
        "cif-structure-analysis",
        "limitations",
        "IUCr dictionary licensing and full portal enumeration remain unresolved.",
        "IUCr dictionary byte identity and full portal enumeration remain unresolved.",
    ),
    (
        "cp2k-rigorous-calculations",
        "limitations",
        "The exact-release source catalog is deliberately bounded and the central documentation license identity remains unresolved.",
        "The exact-release source catalog is deliberately bounded and the central documentation corpus identity remains unresolved.",
    ),
    (
        "dft-hpc-execution",
        "blockers",
        "Slurm documentation licensing, the OpenPBS ngpus rendering assumption, repository licensing, and central processor attestation remain unresolved.",
        "Slurm documentation snapshot identity, the OpenPBS ngpus rendering assumption, repository snapshot identity, and central processor attestation remain unresolved.",
    ),
    (
        "dft-project-orchestrator",
        "blockers",
        "Repository licensing and exact JSON Schema redistribution review remain incomplete.",
        "Repository snapshot identity and exact JSON Schema specification-body identity remain incomplete.",
    ),
    (
        "dft-reporting",
        "blockers",
        "The repository has no root license record that closes redistribution of a repository snapshot.",
        "The repository has no root-level byte-identity record that closes an exact repository snapshot.",
    ),
    (
        "dft-review-response",
        "blockers",
        "Repository licensing, semantic closure, and an attested central pack-processor run remain unresolved.",
        "Repository snapshot identity, semantic closure, and an attested central pack-processor run remain unresolved.",
    ),
    (
        "gaussian-rigorous-calculations",
        "limitations",
        "Licensed manuals, examples, binaries, basis payloads, checkpoints, user data, calculation artifacts, execution authorization, convergence, and scientific acceptance remain outside this pack.",
        "Private manuals, examples, binaries, basis payloads, checkpoints, user data, calculation artifacts, execution authorization, convergence, and scientific acceptance remain outside this pack.",
    ),
    (
        "gpumd-rigorous-simulations",
        "blockers",
        "Native GPU build/runtime identity and independent model/data license and provenance closure remain absent.",
        "Native GPU build/runtime identity and independent model/data byte-identity and provenance closure remain absent.",
    ),
    (
        "lasp-rigorous-simulations",
        "blockers",
        "Complete software, interface, model, dataset, and redistribution terms are unavailable from the HTTPS literature.",
        "Complete software, interface, model, dataset, and external-access artifact identities are unavailable from the HTTPS literature.",
    ),
    (
        "literature-to-dft-plan",
        "blockers",
        "Every real source still requires its own exact official-source record, authority resolution, content identity, and license review.",
        "Every real source still requires its own exact official-source record, authority resolution, content identity, and retrieval receipt.",
    ),
    (
        "literature-to-dft-plan",
        "blockers",
        "Repository licensing, semantic closure, and an attested central pack-processor run remain unresolved.",
        "Repository snapshot identity, semantic closure, and an attested central pack-processor run remain unresolved.",
    ),
    (
        "lobster-bonding-analysis",
        "blockers",
        "The exact first-party LOBSTER 5.1.1 version and license pages require query-bearing HTTPS locators, while the central authority contract keeps query_policy forbidden.",
        "The exact first-party LOBSTER 5.1.1 version and access pages require query-bearing HTTPS locators, while the central authority contract keeps query_policy forbidden.",
    ),
    (
        "ml-potential-workflows",
        "blockers",
        "MACE has no exact v0.3.16 documentation corpus and its docs branch has a different revision and restrictive license.",
        "MACE has no exact v0.3.16 documentation corpus, and its docs branch has a different revision and independent source identity.",
    ),
    (
        "ml-potential-workflows",
        "blockers",
        "FairChem v1 generated AutoAPI/missing page and unresolved legacy checkpoint rights prevent complete coverage.",
        "FairChem v1 generated AutoAPI/missing page and unresolved legacy checkpoint byte identities prevent complete coverage.",
    ),
    (
        "ml-potential-workflows",
        "blockers",
        "UMA model-card, reference YAML, checkpoint byte identities, and custom terms remain gated or unresolved.",
        "UMA model-card, reference YAML, checkpoint byte identities, and gated-access records remain unavailable or unresolved.",
    ),
    (
        "ml-potential-workflows",
        "blockers",
        "External FairChem dataset archive identities and reference-DFT software, potential, raw-output, and gated-storage rights remain unresolved.",
        "External FairChem dataset archive identities and reference-DFT software, potential, raw-output, and gated-storage provenance remain unresolved.",
    ),
    (
        "ml-potential-workflows",
        "limitations",
        "MACE framework and docs revisions/licenses are intentionally separate.",
        "MACE framework and docs revisions and source identities are intentionally separate.",
    ),
    (
        "ml-potential-workflows",
        "limitations",
        "FairChem v1, FairChem v2, UMA model artifacts, datasets, and reference-DFT rights are intentionally separate.",
        "FairChem v1, FairChem v2, UMA model artifacts, datasets, and reference-DFT identities are intentionally separate.",
    ),
    (
        "multiwfn-wavefunction-analysis",
        "blockers",
        "Custom license and derivative-manual storage/redistribution rights remain unresolved.",
        "Private manual access and derived-manual storage identities remain unresolved.",
    ),
    (
        "ovito-atomistic-analysis",
        "blockers",
        "Standalone module, Basic desktop, Pro desktop/ovitos, entitlement, activation, third-party terms, and user artifacts remain separate authority and license surfaces.",
        "Standalone module, Basic desktop, Pro desktop/ovitos, entitlement, activation, third-party components, and user artifacts remain separate authority and identity surfaces.",
    ),
    (
        "vaspkit-postprocess",
        "blockers",
        "Documentation storage and derivative redistribution rights are unresolved.",
        "Documentation storage and derived-document byte identities are unresolved.",
    ),
)

SPECIALIZED_SEED_TEXT_ACTIONS: tuple[tuple[str, str, str, str], ...] = (
    (
        "qe-rigorous-calculations",
        "limitations",
        "This metadata-only pack is bounded to the exact QE 7.5 input-manual catalog and remains below complete resolver, processor, license, portal, PDF, link, and asset assurance.",
        "This metadata-only pack is bounded to the exact QE 7.5 input-manual catalog and remains below complete resolver, processor, portal, PDF, link, and asset identity assurance.",
    ),
)

if len(SEED_TEXT_ACTIONS) != EXPECTED_LEGACY_SEED_ACTIONS:
    raise RuntimeError("exact declarative-provider seed ledger count drift")


class ApplyMigrationError(RuntimeError):
    """Fail-closed repository migration error."""


@dataclass(frozen=True)
class ProviderInput:
    seed_path: Path
    scope_path: Path
    catalog_path: Path
    provider: dict[str, Any]
    seed: dict[str, Any]
    scope: dict[str, Any]
    catalog: dict[str, Any]
    catalog_bytes: bytes


@dataclass(frozen=True)
class V11TechnicalLocatorRepair:
    provider_input_id: str
    old_origin: str
    authority_root: str
    expected_excluded_sources: int


CP2K_MANUAL_LOCATOR_REPAIR = V11TechnicalLocatorRepair(
    provider_input_id="cp2k-manual",
    old_origin="https://manual.cp2k.org/",
    authority_root="https://manual.cp2k.org/cp2k-2026_2-branch/",
    expected_excluded_sources=2860,
)


@dataclass(frozen=True)
class MigrationPlan:
    root: Path
    status: str
    seed_paths: tuple[Path, ...]
    provider_inputs: tuple[ProviderInput, ...]
    catalog_after: dict[Path, bytes]
    scope_after: dict[Path, bytes]
    seed_after: dict[Path, bytes]
    changes: dict[Path, bytes]


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ApplyMigrationError(f"JSON_INVALID: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ApplyMigrationError(f"JSON_OBJECT_REQUIRED: {path}")
    return value


def _resolve_ref(root: Path, ref: dict[str, Any], owner: Path) -> Path:
    raw_path = ref.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        raise ApplyMigrationError(f"REF_PATH_INVALID: {owner}")
    posix_path = PurePosixPath(raw_path)
    if posix_path.is_absolute() or ".." in posix_path.parts:
        raise ApplyMigrationError(f"REF_PATH_UNSAFE: {owner}: {raw_path}")
    target = (root / Path(*posix_path.parts)).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ApplyMigrationError(f"REF_PATH_OUTSIDE_ROOT: {owner}: {raw_path}") from exc
    expected_sha = ref.get("sha256")
    if not isinstance(expected_sha, str) or len(expected_sha) != 64:
        raise ApplyMigrationError(f"REF_SHA256_INVALID: {owner}: {raw_path}")
    try:
        actual_sha = _sha256(target.read_bytes())
    except OSError as exc:
        raise ApplyMigrationError(f"REF_READ_FAILED: {owner}: {raw_path}: {exc}") from exc
    if actual_sha != expected_sha:
        raise ApplyMigrationError(
            f"REF_SHA256_MISMATCH: {owner}: {raw_path}: "
            f"expected={expected_sha} actual={actual_sha}"
        )
    return target


def enumerate_provider_inputs(root: Path) -> tuple[tuple[Path, ...], tuple[ProviderInput, ...]]:
    """Enumerate the migration universe exclusively through the 26 seed files."""

    seed_paths = tuple(sorted(root.glob("skills/*/references/source-pack-seed.json")))
    if len(seed_paths) != EXPECTED_SEEDS:
        raise ApplyMigrationError(
            f"SEED_COUNT_MISMATCH: expected={EXPECTED_SEEDS} actual={len(seed_paths)}"
        )

    provider_inputs: list[ProviderInput] = []
    seen_catalog_paths: set[Path] = set()
    seen_input_ids: set[tuple[str, str]] = set()
    for seed_path in seed_paths:
        seed = _load_json(seed_path)
        skill_id = seed.get("skill_id")
        if not isinstance(skill_id, str) or not skill_id:
            raise ApplyMigrationError(f"SEED_SKILL_ID_INVALID: {seed_path}")
        scope_ref = seed.get("scope_catalog_ref")
        if not isinstance(scope_ref, dict):
            raise ApplyMigrationError(f"SCOPE_REF_INVALID: {seed_path}")
        scope_path = _resolve_ref(root, scope_ref, seed_path)
        scope = _load_json(scope_path)
        providers = seed.get("providers")
        if not isinstance(providers, list):
            raise ApplyMigrationError(f"SEED_PROVIDERS_INVALID: {seed_path}")
        for provider in providers:
            if not isinstance(provider, dict):
                raise ApplyMigrationError(f"SEED_PROVIDER_INVALID: {seed_path}")
            if provider.get("adapter_id") != "declarative-catalog-v1":
                continue
            input_id = provider.get("input_id")
            input_key = (skill_id, input_id) if isinstance(input_id, str) else None
            if input_key is None or input_key in seen_input_ids:
                raise ApplyMigrationError(f"PROVIDER_INPUT_ID_DUPLICATE: {input_id!r}")
            source_ref = provider.get("source_ref")
            if not isinstance(source_ref, dict):
                raise ApplyMigrationError(f"SOURCE_REF_INVALID: {seed_path}: {input_id}")
            catalog_path = _resolve_ref(root, source_ref, seed_path)
            if catalog_path in seen_catalog_paths:
                raise ApplyMigrationError(f"CATALOG_PATH_DUPLICATE: {catalog_path}")
            catalog_bytes = catalog_path.read_bytes()
            provider_inputs.append(
                ProviderInput(
                    seed_path=seed_path,
                    scope_path=scope_path,
                    catalog_path=catalog_path,
                    provider=provider,
                    seed=seed,
                    scope=scope,
                    catalog=_load_json(catalog_path),
                    catalog_bytes=catalog_bytes,
                )
            )
            seen_input_ids.add(input_key)
            seen_catalog_paths.add(catalog_path)

    if len(provider_inputs) != EXPECTED_DECLARATIVE_CATALOGS:
        raise ApplyMigrationError(
            "DECLARATIVE_CATALOG_COUNT_MISMATCH: "
            f"expected={EXPECTED_DECLARATIVE_CATALOGS} actual={len(provider_inputs)}"
        )
    return seed_paths, tuple(provider_inputs)


def _authority_projections(root: Path) -> dict[str, dict[str, Any]]:
    authorities = load_yaml_strict(
        root / "registry" / "official-source-authorities.yaml",
        "official-source-authorities.yaml",
    )
    software = load_yaml_strict(
        root / "registry" / "software-registry.yaml",
        "software-registry.yaml",
    )
    failures, projections = validate_and_project(
        authorities,
        software_data=software,
        source_root=root,
    )
    if failures:
        raise ApplyMigrationError(
            "AUTHORITY_REGISTRY_INVALID: " + " | ".join(str(item) for item in failures)
        )
    return projections


def _schema_validator(root: Path, name: str) -> Draft202012Validator:
    return Draft202012Validator(
        _load_json(root / "contracts" / name),
        format_checker=FormatChecker(),
    )


def _validate_schema(
    validator: Draft202012Validator,
    value: dict[str, Any],
    path: Path,
    code: str,
) -> None:
    errors = sorted(
        validator.iter_errors(value),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if not errors:
        return
    first = errors[0]
    location = "/" + "/".join(str(part) for part in first.absolute_path)
    raise ApplyMigrationError(f"{code}: {path}: {location}: {first.message}")


def _relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _legacy_record_hits(
    action: Any,
    item: ProviderInput,
) -> int:
    collection_keys = {
        "blocker": ("blockers", "code"),
        "loss": ("losses", "loss_id"),
        "subject": ("subjects", "subject_id"),
        "exclusion": ("reviewed_exclusions", "source_id"),
    }
    if action.record_type == "limitation":
        return item.catalog.get("limitations", []).count(action.record_id)
    collection, identity_key = collection_keys[action.record_type]
    hits = 0
    for record in item.catalog.get(collection, []):
        if not isinstance(record, dict) or record.get(identity_key) != action.record_id:
            continue
        if _sha256(canonical_projection_bytes(record)) != action.expected_sha256:
            raise ApplyMigrationError(
                "LEGACY_LEDGER_RECORD_DRIFT: "
                f"{item.catalog_path}: {action.record_type}: {action.record_id}"
            )
        hits += 1
    return hits


def _audit_legacy_catalog_ledger(provider_inputs: tuple[ProviderInput, ...]) -> None:
    """Require every reviewed typed action to match one catalog and scope record."""

    for action in LEGACY_RECORD_ACTIONS:
        record_hits = 0
        scope_hits = 0
        for item in provider_inputs:
            if item.provider.get("input_id") != action.provider_input_id:
                continue
            record_hits += _legacy_record_hits(action, item)
            if action.record_type != "subject":
                continue
            for subject in item.scope.get("subjects", []):
                if not isinstance(subject, dict):
                    continue
                if subject.get("subject_id") != action.record_id:
                    continue
                if action.provider_input_id not in subject.get("provider_input_ids", []):
                    continue
                if subject.get("statement") != action.expected_scope_statement:
                    raise ApplyMigrationError(
                        "LEGACY_LEDGER_SCOPE_DRIFT: "
                        f"{item.scope_path}: {action.provider_input_id}: {action.record_id}"
                    )
                scope_hits += 1
        if record_hits != 1:
            raise ApplyMigrationError(
                "LEGACY_LEDGER_RECORD_CONSUMPTION: "
                f"{action.record_type}:{action.provider_input_id}:{action.record_id}: "
                f"expected=1 actual={record_hits}"
            )
        if action.record_type == "subject" and scope_hits != 1:
            raise ApplyMigrationError(
                "LEGACY_LEDGER_SCOPE_CONSUMPTION: "
                f"{action.provider_input_id}:{action.record_id}: "
                f"expected=1 actual={scope_hits}"
            )


def _scope_action_map() -> dict[tuple[str, str], Any]:
    return {
        (action.provider_input_id, action.record_id): action
        for action in LEGACY_RECORD_ACTIONS
        if action.record_type == "subject"
    }


def _migrate_scopes(
    root: Path,
    provider_inputs: tuple[ProviderInput, ...],
    catalog_payloads: dict[Path, dict[str, Any]],
    catalog_after: dict[Path, bytes],
) -> dict[Path, bytes]:
    """Synchronize exact subject actions and catalog origin identities."""

    scope_items: dict[Path, list[ProviderInput]] = {}
    for item in provider_inputs:
        scope_items.setdefault(item.scope_path, []).append(item)

    all_seed_scopes = {
        item.scope_path: item.scope
        for item in provider_inputs
    }
    # QE and VASP scopes have no declarative ProviderInput, so enumerate them
    # through their seeds without using a scope filename glob.
    for seed_path in sorted(root.glob("skills/*/references/source-pack-seed.json")):
        seed = _load_json(seed_path)
        scope_path = _resolve_ref(root, seed["scope_catalog_ref"], seed_path)
        all_seed_scopes.setdefault(scope_path, _load_json(scope_path))
    if len(all_seed_scopes) != EXPECTED_SCOPE_CATALOGS:
        raise ApplyMigrationError(
            f"SCOPE_COUNT_MISMATCH: expected={EXPECTED_SCOPE_CATALOGS} "
            f"actual={len(all_seed_scopes)}"
        )

    catalog_hashes = {
        _relative_path(root, path): _sha256(payload)
        for path, payload in catalog_after.items()
    }
    actions = _scope_action_map()
    action_hits: dict[tuple[str, str], int] = {}
    scope_after: dict[Path, bytes] = {}

    for scope_path, original_scope in sorted(all_seed_scopes.items()):
        scope = copy.deepcopy(original_scope)
        migrated_subjects: list[dict[str, Any]] = []
        for raw_subject in scope.get("subjects", []):
            if not isinstance(raw_subject, dict):
                raise ApplyMigrationError(f"SCOPE_SUBJECT_INVALID: {scope_path}")
            subject = copy.deepcopy(raw_subject)
            subject_id = subject.get("subject_id")
            provider_ids = subject.get("provider_input_ids", [])
            matching = [
                actions[(provider_id, subject_id)]
                for provider_id in provider_ids
                if (provider_id, subject_id) in actions
            ]
            if matching:
                if len(matching) != len(provider_ids):
                    raise ApplyMigrationError(
                        f"SCOPE_SUBJECT_ACTION_PARTIAL: {scope_path}: {subject_id}"
                    )
                for action in matching:
                    key = (action.provider_input_id, action.record_id)
                    action_hits[key] = action_hits.get(key, 0) + 1
                    if subject.get("statement") != action.expected_scope_statement:
                        raise ApplyMigrationError(
                            f"SCOPE_SUBJECT_STATEMENT_DRIFT: {scope_path}: {key}"
                        )
                kinds = {action.action for action in matching}
                if kinds == {"drop"}:
                    continue
                replacement_ids = {action.replacement_id for action in matching}
                replacement_statements = {
                    action.replacement_statement for action in matching
                }
                if (
                    kinds != {"rename"}
                    or len(replacement_ids) != 1
                    or len(replacement_statements) != 1
                    or None in replacement_ids
                    or None in replacement_statements
                ):
                    raise ApplyMigrationError(
                        f"SCOPE_SUBJECT_ACTION_CONFLICT: {scope_path}: {subject_id}"
                    )
                subject["subject_id"] = next(iter(replacement_ids))
                subject["statement"] = next(iter(replacement_statements))

            for origin_ref in subject.get("origin_refs", []):
                if not isinstance(origin_ref, dict):
                    raise ApplyMigrationError(
                        f"SCOPE_ORIGIN_REF_INVALID: {scope_path}: {subject_id}"
                    )
                origin_path = origin_ref.get("path")
                if origin_path in catalog_hashes:
                    origin_ref["sha256"] = catalog_hashes[origin_path]
            migrated_subjects.append(subject)

        for item in scope_items.get(scope_path, []):
            input_id = str(item.provider["input_id"])
            binding = CATALOG_WIDE_TECHNICAL_BINDINGS.get(input_id)
            if binding is None:
                continue
            relative_catalog = _relative_path(root, item.catalog_path)
            migrated_subjects.append(
                {
                    "subject_id": binding["subject_id"],
                    "subject_kind": "documented-claim",
                    "evidence_class": "official-provider-required",
                    "origin_refs": [
                        {
                            "path": relative_catalog,
                            "sha256": catalog_hashes[relative_catalog],
                        }
                    ],
                    "statement": binding["statement"],
                    "expected_disposition": "partial",
                    "provider_input_ids": [input_id],
                }
            )

        subject_ids = [subject.get("subject_id") for subject in migrated_subjects]
        if len(subject_ids) != len(set(subject_ids)):
            raise ApplyMigrationError(f"SCOPE_SUBJECT_DUPLICATE: {scope_path}")
        scope["subjects"] = migrated_subjects
        scope_after[scope_path] = canonical_json_bytes(scope)

    expected_scope_actions = {
        (action.provider_input_id, action.record_id)
        for action in LEGACY_RECORD_ACTIONS
        if action.record_type == "subject"
    }
    if set(action_hits) != expected_scope_actions or any(
        count != 1 for count in action_hits.values()
    ):
        raise ApplyMigrationError(
            "SCOPE_ACTION_CONSUMPTION_MISMATCH: "
            f"expected={len(expected_scope_actions)} actual={len(action_hits)}"
        )
    return scope_after


def _apply_seed_text_actions(
    seed: dict[str, Any],
    actions: tuple[tuple[str, str, str, str], ...],
    hits: dict[tuple[str, str, str], int],
) -> None:
    skill_id = seed.get("skill_id")
    for action_skill, collection, old_text, replacement_text in actions:
        if skill_id != action_skill:
            continue
        values = seed.get(collection)
        if not isinstance(values, list):
            raise ApplyMigrationError(
                f"SEED_TEXT_COLLECTION_INVALID: {skill_id}: {collection}"
            )
        count = values.count(old_text)
        key = (action_skill, collection, old_text)
        hits[key] = hits.get(key, 0) + count
        if count != 1:
            raise ApplyMigrationError(
                f"SEED_TEXT_ACTION_CONSUMPTION: {skill_id}: {collection}: "
                f"expected=1 actual={count}"
            )
        values[values.index(old_text)] = replacement_text


def _migrate_seeds(
    root: Path,
    seed_paths: tuple[Path, ...],
    catalog_after: dict[Path, bytes],
    scope_after: dict[Path, bytes],
) -> dict[Path, bytes]:
    catalog_hashes = {
        _relative_path(root, path): _sha256(payload)
        for path, payload in catalog_after.items()
    }
    scope_hashes = {
        _relative_path(root, path): _sha256(payload)
        for path, payload in scope_after.items()
    }
    declarative_hits: dict[tuple[str, str, str], int] = {}
    specialized_hits: dict[tuple[str, str, str], int] = {}
    seed_after: dict[Path, bytes] = {}
    for seed_path in seed_paths:
        seed = copy.deepcopy(_load_json(seed_path))
        _apply_seed_text_actions(seed, SEED_TEXT_ACTIONS, declarative_hits)
        _apply_seed_text_actions(
            seed,
            SPECIALIZED_SEED_TEXT_ACTIONS,
            specialized_hits,
        )
        scope_ref = seed.get("scope_catalog_ref")
        scope_ref["sha256"] = scope_hashes[scope_ref["path"]]
        for provider in seed.get("providers", []):
            ref = provider.get("source_ref")
            if provider.get("adapter_id") == "declarative-catalog-v1":
                ref["sha256"] = catalog_hashes[ref["path"]]
        seed_after[seed_path] = canonical_json_bytes(seed)

    expected_declarative = {
        (skill_id, collection, old)
        for skill_id, collection, old, _replacement in SEED_TEXT_ACTIONS
    }
    expected_specialized = {
        (skill_id, collection, old)
        for skill_id, collection, old, _replacement
        in SPECIALIZED_SEED_TEXT_ACTIONS
    }
    if (
        set(declarative_hits) != expected_declarative
        or any(count != 1 for count in declarative_hits.values())
    ):
        raise ApplyMigrationError(
            "DECLARATIVE_SEED_ACTION_CONSUMPTION_MISMATCH: "
            f"expected={len(expected_declarative)} actual={len(declarative_hits)}"
        )
    if (
        set(specialized_hits) != expected_specialized
        or any(count != 1 for count in specialized_hits.values())
    ):
        raise ApplyMigrationError(
            "SPECIALIZED_SEED_ACTION_CONSUMPTION_MISMATCH: "
            f"expected={len(expected_specialized)} actual={len(specialized_hits)}"
        )
    return seed_after


def _validate_final_graph(
    root: Path,
    seed_paths: tuple[Path, ...],
    catalog_payloads: dict[Path, dict[str, Any]],
    catalog_after: dict[Path, bytes],
    scope_after: dict[Path, bytes],
    seed_after: dict[Path, bytes],
) -> None:
    catalog_validator = _schema_validator(
        root, "official-document-source-catalog-1.1.schema.json"
    )
    scope_validator = _schema_validator(
        root, "official-document-scope-catalog.schema.json"
    )
    seed_validator = _schema_validator(
        root, "official-document-pack-seed.schema.json"
    )
    for path, payload in catalog_after.items():
        catalog = catalog_payloads[path]
        _validate_schema(catalog_validator, catalog, path, "CATALOG_SCHEMA_INVALID")
        if "license" in catalog:
            raise ApplyMigrationError(f"CATALOG_TOP_LEVEL_LICENSE_FORBIDDEN: {path}")
        if not catalog.get("limitations"):
            raise ApplyMigrationError(f"CATALOG_LIMITATION_REQUIRED: {path}")

    prospective = {**catalog_after, **scope_after, **seed_after}
    provider_catalog: dict[tuple[Path, str], Path] = {}
    for seed_path in seed_paths:
        seed = json.loads(seed_after[seed_path])
        _validate_schema(seed_validator, seed, seed_path, "SEED_SCHEMA_INVALID")
        scope_path = _resolve_path_without_hash(root, seed["scope_catalog_ref"], seed_path)
        expected_scope_hash = _sha256(prospective.get(scope_path, scope_path.read_bytes()))
        if seed["scope_catalog_ref"]["sha256"] != expected_scope_hash:
            raise ApplyMigrationError(f"SEED_SCOPE_HASH_MISMATCH: {seed_path}")
        for provider in seed["providers"]:
            ref = provider["source_ref"]
            source_path = _resolve_path_without_hash(root, ref, seed_path)
            actual = prospective.get(source_path, source_path.read_bytes())
            if ref["sha256"] != _sha256(actual):
                raise ApplyMigrationError(
                    f"SEED_SOURCE_HASH_MISMATCH: {seed_path}: {ref['path']}"
                )
            if provider["adapter_id"] == "declarative-catalog-v1":
                provider_catalog[(scope_path, provider["input_id"])] = source_path

    for scope_path, payload in scope_after.items():
        scope = json.loads(payload)
        _validate_schema(scope_validator, scope, scope_path, "SCOPE_SCHEMA_INVALID")
        provider_subjects: dict[str, set[str]] = {}
        for subject in scope["subjects"]:
            for origin_ref in subject["origin_refs"]:
                origin_path = _resolve_path_without_hash(root, origin_ref, scope_path)
                actual = prospective.get(origin_path, origin_path.read_bytes())
                if origin_ref["sha256"] != _sha256(actual):
                    raise ApplyMigrationError(
                        f"SCOPE_ORIGIN_HASH_MISMATCH: {scope_path}: "
                        f"{origin_ref['path']}"
                    )
            if subject["evidence_class"] != "official-provider-required":
                continue
            for input_id in subject["provider_input_ids"]:
                provider_subjects.setdefault(input_id, set()).add(
                    subject["subject_id"]
                )
        for (candidate_scope, input_id), catalog_path in provider_catalog.items():
            if candidate_scope != scope_path:
                continue
            catalog_subjects = set(catalog_payloads[catalog_path]["subjects"])
            if provider_subjects.get(input_id, set()) != catalog_subjects:
                raise ApplyMigrationError(
                    "SCOPE_CATALOG_SUBJECT_CLOSURE_MISMATCH: "
                    f"{scope_path}: {input_id}: "
                    f"scope={sorted(provider_subjects.get(input_id, set()))} "
                    f"catalog={sorted(catalog_subjects)}"
                )
        unknown_provider_ids = set(provider_subjects) - {
            input_id
            for candidate_scope, input_id in provider_catalog
            if candidate_scope == scope_path
        }
        # Specialized QE/VASP provider IDs have no declarative v1.1 catalog and
        # therefore are outside this declarative subject-closure comparison.
        if unknown_provider_ids and scope_path in {
            (root / "skills/qe-rigorous-calculations/references/source-pack-scope-catalog.json").resolve(),
            (root / "skills/vasp-rigorous-calculations/references/source-pack-scope-catalog.json").resolve(),
        }:
            unknown_provider_ids.clear()
        if unknown_provider_ids:
            raise ApplyMigrationError(
                f"SCOPE_PROVIDER_WITHOUT_CATALOG: {scope_path}: "
                f"{sorted(unknown_provider_ids)}"
            )


def _resolve_path_without_hash(root: Path, ref: dict[str, Any], owner: Path) -> Path:
    raw_path = ref.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        raise ApplyMigrationError(f"REF_PATH_INVALID: {owner}")
    posix_path = PurePosixPath(raw_path)
    if posix_path.is_absolute() or ".." in posix_path.parts:
        raise ApplyMigrationError(f"REF_PATH_UNSAFE: {owner}: {raw_path}")
    target = (root / Path(*posix_path.parts)).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ApplyMigrationError(f"REF_PATH_OUTSIDE_ROOT: {owner}: {raw_path}") from exc
    return target


def _repair_cp2k_manual_v11_catalog(
    item: ProviderInput,
    authority_projection: dict[str, Any],
) -> tuple[dict[str, Any], bytes]:
    """Repair exactly the reviewed CP2K excluded-locator legacy state."""

    repair = CP2K_MANUAL_LOCATOR_REPAIR
    if item.provider.get("input_id") != repair.provider_input_id:
        return item.catalog, item.catalog_bytes
    if item.catalog.get("authority_root") != repair.authority_root:
        raise ApplyMigrationError(
            f"CP2K_LOCATOR_REPAIR_AUTHORITY_ROOT_DRIFT: {item.catalog_path}"
        )
    expected_origin = repair.old_origin.rstrip("/")
    expected_prefix = urlsplit(repair.authority_root).path
    if (
        expected_origin not in authority_projection.get("allowed_https_origins", [])
        or expected_prefix
        not in authority_projection.get("allowed_path_prefixes", [])
        or repair.authority_root
        not in authority_projection.get("canonical_urls", [])
    ):
        raise ApplyMigrationError(
            f"CP2K_LOCATOR_REPAIR_AUTHORITY_DRIFT: {item.catalog_path}"
        )
    upstream = (
        authority_projection.get("canonical_snapshot", {})
        .get("upstream_sources_by_id")
    )
    discovered = item.catalog.get("discovered_sources")
    if not isinstance(upstream, dict) or not isinstance(discovered, dict):
        raise ApplyMigrationError(
            f"CP2K_LOCATOR_REPAIR_INVENTORY_INVALID: {item.catalog_path}"
        )

    catalog = copy.deepcopy(item.catalog)
    legacy_ids: list[str] = []
    repaired_ids: list[str] = []
    excluded_count = 0

    def canonical_source_path(source_id: str, locator: object) -> str | None:
        upstream_entry = upstream.get(source_id)
        direct_path = (
            upstream_entry.get("source_path")
            if isinstance(upstream_entry, dict)
            else None
        )
        if isinstance(direct_path, str) and direct_path:
            return direct_path
        if not isinstance(locator, str):
            return None
        for base in (repair.old_origin, repair.authority_root):
            if not locator.startswith(base):
                continue
            candidate = locator[len(base) :]
            canonical_entry = upstream.get(cp2k_source_id(candidate))
            canonical_path = (
                canonical_entry.get("source_path")
                if isinstance(canonical_entry, dict)
                else None
            )
            if canonical_path == candidate:
                return candidate
        return None

    for source_id, source in catalog["discovered_sources"].items():
        if not isinstance(source, dict):
            raise ApplyMigrationError(
                f"CP2K_LOCATOR_REPAIR_SOURCE_INVALID: {item.catalog_path}: {source_id}"
            )
        content = source.get("content")
        if not isinstance(content, dict):
            continue
        if (
            content.get("content_mode") == "excluded"
            and source.get("disposition") != "excluded"
        ):
            raise ApplyMigrationError(
                f"CP2K_LOCATOR_REPAIR_NONEXCLUDED: {item.catalog_path}: {source_id}"
            )
        if source.get("disposition") != "excluded":
            source_path = canonical_source_path(source_id, content.get("locator"))
            if (
                isinstance(source_path, str)
                and content.get("locator") == repair.old_origin + source_path
            ):
                raise ApplyMigrationError(
                    f"CP2K_LOCATOR_REPAIR_NONEXCLUDED: "
                    f"{item.catalog_path}: {source_id}"
                )
            continue
        excluded_count += 1
        if content.get("content_mode") != "excluded":
            raise ApplyMigrationError(
                f"CP2K_LOCATOR_REPAIR_CONTENT_MODE_DRIFT: {item.catalog_path}: {source_id}"
            )
        locator = content.get("locator")
        source_path = canonical_source_path(source_id, locator)
        if (
            not isinstance(source_path, str)
            or not source_path
            or not isinstance(locator, str)
        ):
            raise ApplyMigrationError(
                f"CP2K_LOCATOR_REPAIR_LOCATOR_INVALID: {item.catalog_path}: {source_id}"
            )
        parsed = urlsplit(locator)
        if parsed.query or parsed.fragment:
            raise ApplyMigrationError(
                f"CP2K_LOCATOR_REPAIR_QUERY_FRAGMENT_DRIFT: {item.catalog_path}: {source_id}"
            )
        legacy_locator = repair.old_origin + source_path
        repaired_locator = repair.authority_root + source_path
        if locator == legacy_locator:
            legacy_ids.append(source_id)
        elif locator == repaired_locator:
            repaired_ids.append(source_id)
        else:
            raise ApplyMigrationError(
                f"CP2K_LOCATOR_REPAIR_LOCATOR_DRIFT: {item.catalog_path}: {source_id}"
            )

    if legacy_ids and repaired_ids:
        raise ApplyMigrationError(
            "CP2K_LOCATOR_REPAIR_MIXED_STATE: "
            f"{item.catalog_path}: legacy={len(legacy_ids)} repaired={len(repaired_ids)}"
        )
    if legacy_ids and excluded_count != repair.expected_excluded_sources:
        raise ApplyMigrationError(
            "CP2K_LOCATOR_REPAIR_COUNT_DRIFT: "
            f"{item.catalog_path}: expected={repair.expected_excluded_sources} "
            f"actual={excluded_count}"
        )
    if legacy_ids and len(legacy_ids) != repair.expected_excluded_sources:
        raise ApplyMigrationError(
            f"CP2K_LOCATOR_REPAIR_STATE_INVALID: {item.catalog_path}"
        )
    if not legacy_ids and len(repaired_ids) != excluded_count:
        raise ApplyMigrationError(
            f"CP2K_LOCATOR_REPAIR_STATE_INVALID: {item.catalog_path}"
        )
    for source_id in legacy_ids:
        source_path = upstream[source_id]["source_path"]
        catalog["discovered_sources"][source_id]["content"]["locator"] = (
            repair.authority_root + source_path
        )
    discovery_processor = catalog.get("discovery_processor")
    if not isinstance(discovery_processor, dict):
        raise ApplyMigrationError(
            f"CP2K_LOCATOR_REPAIR_PROCESSOR_INVALID: {item.catalog_path}"
        )
    discovery_processor["output_sha256"] = _sha256(
        canonical_projection_bytes(catalog["discovered_sources"])
    )
    if catalog == item.catalog:
        return item.catalog, item.catalog_bytes
    return catalog, canonical_json_bytes(catalog)


def _refresh_v11_repair_hashes(
    root: Path,
    item: ProviderInput,
    catalog_bytes: bytes,
) -> tuple[bytes, bytes]:
    relative_catalog = _relative_path(root, item.catalog_path)
    catalog_sha = _sha256(catalog_bytes)
    scope = copy.deepcopy(item.scope)
    origin_hits = 0
    for subject in scope.get("subjects", []):
        for origin_ref in subject.get("origin_refs", []):
            if origin_ref.get("path") == relative_catalog:
                origin_ref["sha256"] = catalog_sha
                origin_hits += 1
    if origin_hits == 0:
        raise ApplyMigrationError(
            f"CP2K_LOCATOR_REPAIR_SCOPE_REF_MISSING: {item.scope_path}"
        )
    scope_bytes = canonical_json_bytes(scope)

    seed = copy.deepcopy(item.seed)
    provider_hits = 0
    for provider in seed.get("providers", []):
        if provider.get("input_id") != CP2K_MANUAL_LOCATOR_REPAIR.provider_input_id:
            continue
        ref = provider.get("source_ref")
        if not isinstance(ref, dict) or ref.get("path") != relative_catalog:
            raise ApplyMigrationError(
                f"CP2K_LOCATOR_REPAIR_SEED_SOURCE_REF_DRIFT: {item.seed_path}"
            )
        ref["sha256"] = catalog_sha
        provider_hits += 1
    if provider_hits != 1:
        raise ApplyMigrationError(
            f"CP2K_LOCATOR_REPAIR_SEED_PROVIDER_COUNT: {item.seed_path}: {provider_hits}"
        )
    scope_ref = seed.get("scope_catalog_ref")
    if (
        not isinstance(scope_ref, dict)
        or scope_ref.get("path") != _relative_path(root, item.scope_path)
    ):
        raise ApplyMigrationError(
            f"CP2K_LOCATOR_REPAIR_SEED_SCOPE_REF_DRIFT: {item.seed_path}"
        )
    scope_ref["sha256"] = _sha256(scope_bytes)
    return scope_bytes, canonical_json_bytes(seed)


def build_plan(root: Path) -> MigrationPlan:
    """Build and schema-validate every prospective catalog byte before writes."""

    root = root.resolve()
    seed_paths, provider_inputs = enumerate_provider_inputs(root)
    versions = {item.catalog.get("schema_version") for item in provider_inputs}
    if versions == {"1.1"}:
        projections = _authority_projections(root)
        catalog_after = {
            item.catalog_path: item.catalog_bytes for item in provider_inputs
        }
        catalog_payloads = {
            item.catalog_path: item.catalog for item in provider_inputs
        }
        scope_after: dict[Path, bytes] = {}
        for seed_path in seed_paths:
            seed = _load_json(seed_path)
            scope_path = _resolve_ref(root, seed["scope_catalog_ref"], seed_path)
            scope_after[scope_path] = scope_path.read_bytes()
        seed_after = {path: path.read_bytes() for path in seed_paths}
        repair_items = [
            item
            for item in provider_inputs
            if item.provider.get("input_id")
            == CP2K_MANUAL_LOCATOR_REPAIR.provider_input_id
        ]
        if len(repair_items) != 1:
            raise ApplyMigrationError(
                "CP2K_LOCATOR_REPAIR_PROVIDER_COUNT: "
                f"expected=1 actual={len(repair_items)}"
            )
        repaired_items: list[ProviderInput] = []
        for item in repair_items:
            authority_id = item.provider.get("authority_id")
            if authority_id not in projections:
                raise ApplyMigrationError(
                    f"AUTHORITY_PROJECTION_MISSING: {item.catalog_path}: {authority_id}"
                )
            catalog, payload = _repair_cp2k_manual_v11_catalog(
                item, projections[authority_id]
            )
            catalog_payloads[item.catalog_path] = catalog
            catalog_after[item.catalog_path] = payload
            if payload != item.catalog_bytes:
                repaired_items.append(item)
        if len(repaired_items) > 1:
            raise ApplyMigrationError("CP2K_LOCATOR_REPAIR_PROVIDER_DUPLICATE")
        for item in repaired_items:
            scope_payload, seed_payload = _refresh_v11_repair_hashes(
                root, item, catalog_after[item.catalog_path]
            )
            scope_after[item.scope_path] = scope_payload
            seed_after[item.seed_path] = seed_payload
        _validate_final_graph(
            root,
            seed_paths,
            catalog_payloads,
            catalog_after,
            scope_after,
            seed_after,
        )
        old_seed_text = {
            old
            for _skill, _collection, old, _replacement
            in (*SEED_TEXT_ACTIONS, *SPECIALIZED_SEED_TEXT_ACTIONS)
        }
        for path, payload in seed_after.items():
            seed = json.loads(payload)
            for collection in ("limitations", "blockers"):
                if old_seed_text.intersection(seed.get(collection, [])):
                    raise ApplyMigrationError(f"SEED_LEGACY_TEXT_REMAINS: {path}")
        final_files = {**catalog_after, **scope_after, **seed_after}
        changes = {
            path: payload
            for path, payload in final_files.items()
            if path.read_bytes() != payload
        }
        return MigrationPlan(
            root=root,
            status="migration-required" if changes else "up-to-date",
            seed_paths=seed_paths,
            provider_inputs=provider_inputs,
            catalog_after=catalog_after,
            scope_after=scope_after,
            seed_after=seed_after,
            changes=changes,
        )
    if versions != {"1.0"}:
        raise ApplyMigrationError(
            f"CATALOG_VERSION_SET_INVALID: expected all 1.0 or all 1.1; actual={versions}"
        )

    _audit_legacy_catalog_ledger(provider_inputs)
    projections = _authority_projections(root)
    validator = _schema_validator(
        root, "official-document-source-catalog-1.1.schema.json"
    )
    catalog_after: dict[Path, bytes] = {}
    catalog_payloads: dict[Path, dict[str, Any]] = {}

    for item in provider_inputs:
        included = [
            source
            for source in item.catalog.get("sources", [])
            if isinstance(source, dict) and source.get("disposition") == "included"
        ]
        if not included:
            raise ApplyMigrationError(f"CATALOG_INCLUDED_SOURCE_MISSING: {item.catalog_path}")
        authority_id = item.provider.get("authority_id")
        if authority_id not in projections:
            raise ApplyMigrationError(
                f"AUTHORITY_PROJECTION_MISSING: {item.catalog_path}: {authority_id}"
            )
        try:
            converted = convert_catalog_v10_to_v11(
                item.catalog,
                provider=item.provider,
                authority={"authority_id": authority_id},
                authority_projection=projections[authority_id],
                scope_catalog=item.scope,
                inventory_projection={
                    "locator": included[0]["locator"],
                    "identity": {
                        "sha256": _sha256(item.catalog_bytes),
                        "bytes": len(item.catalog_bytes),
                    },
                    "canonical_preimage_bytes": item.catalog_bytes,
                },
            )
        except MigrationError as exc:
            raise ApplyMigrationError(
                f"CATALOG_CONVERSION_FAILED: {item.catalog_path}: {exc}"
            ) from exc
        _validate_schema(
            validator, converted, item.catalog_path, "CATALOG_SCHEMA_INVALID"
        )
        catalog_payloads[item.catalog_path] = converted
        catalog_after[item.catalog_path] = canonical_json_bytes(converted)

    if len(catalog_after) != EXPECTED_DECLARATIVE_CATALOGS:
        raise ApplyMigrationError(
            f"CATALOG_PLAN_COUNT_MISMATCH: {len(catalog_after)}"
        )
    scope_after = _migrate_scopes(
        root, provider_inputs, catalog_payloads, catalog_after
    )
    seed_after = _migrate_seeds(root, seed_paths, catalog_after, scope_after)
    _validate_final_graph(
        root,
        seed_paths,
        catalog_payloads,
        catalog_after,
        scope_after,
        seed_after,
    )
    final_files = {**catalog_after, **scope_after, **seed_after}
    changes = {
        path: payload
        for path, payload in final_files.items()
        if path.read_bytes() != payload
    }
    return MigrationPlan(
        root=root,
        status="migration-required" if changes else "up-to-date",
        seed_paths=seed_paths,
        provider_inputs=provider_inputs,
        catalog_after=catalog_after,
        scope_after=scope_after,
        seed_after=seed_after,
        changes=changes,
    )


def apply_changes_atomically(
    root: Path,
    changes: dict[Path, bytes],
    *,
    replace: Any = os.replace,
) -> None:
    """Stage all after bytes and restore every touched input on any failure."""

    if not changes:
        return
    root = root.resolve()
    transaction_dir = Path(
        tempfile.mkdtemp(prefix=".official-doc-v11-inputs-", dir=root)
    )
    before_dir = transaction_dir / "before"
    after_dir = transaction_dir / "after"
    before_dir.mkdir()
    after_dir.mkdir()
    ordered = sorted(changes)
    replaced: list[tuple[Path, Path]] = []
    try:
        for index, target in enumerate(ordered):
            if target.is_symlink() or not target.is_file():
                raise ApplyMigrationError(f"TRANSACTION_TARGET_INVALID: {target}")
            before = before_dir / str(index)
            after = after_dir / str(index)
            before.write_bytes(target.read_bytes())
            after.write_bytes(changes[target])
            os.chmod(before, target.stat().st_mode & 0o777)
            os.chmod(after, target.stat().st_mode & 0o777)
            for staged in (before, after):
                with staged.open("rb") as handle:
                    os.fsync(handle.fileno())
        for index, target in enumerate(ordered):
            before = before_dir / str(index)
            after = after_dir / str(index)
            replace(after, target)
            replaced.append((target, before))
        for target in ordered:
            if target.read_bytes() != changes[target]:
                raise ApplyMigrationError(f"TRANSACTION_VERIFY_FAILED: {target}")
    except BaseException:
        restore_failures: list[str] = []
        for target, before in reversed(replaced):
            try:
                replace(before, target)
            except BaseException as restore_exc:
                restore_failures.append(f"{target}: {restore_exc}")
        if restore_failures:
            raise ApplyMigrationError(
                "TRANSACTION_ROLLBACK_FAILED: " + " | ".join(restore_failures)
            )
        raise
    finally:
        shutil.rmtree(transaction_dir, ignore_errors=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true", help="print the validated migration plan")
    mode.add_argument("--check", action="store_true", help="validate without writing")
    mode.add_argument("--apply", action="store_true", help="apply the validated migration")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        plan = build_plan(args.root)
        report = {
            "status": plan.status,
            "seeds": len(plan.seed_paths),
            "declarative_catalogs": len(plan.catalog_after),
            "scopes": len(plan.scope_after),
            "changes": len(plan.changes),
            "paths": [
                _relative_path(plan.root, path) for path in sorted(plan.changes)
            ],
        }
        if args.plan:
            print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
            return 0
        if args.apply:
            apply_changes_atomically(plan.root, plan.changes)
            print(
                json.dumps(
                    {**report, "status": "applied" if plan.changes else "up-to-date"},
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 0
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    except ApplyMigrationError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
