#!/usr/bin/env python3
"""Build the metadata-only CP2K source-pack catalogs.

The default mode writes three deterministic JSON catalogs. ``--check`` is
strictly offline and compares their exact bytes. ``--refresh`` additionally
re-fetches every pinned upstream object and verifies hash/byte identities, but
never stores upstream document bodies.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker


SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[3]
REFERENCES = SKILL_ROOT / "references"
SKILL_ID = "cp2k-rigorous-calculations"
RETRIEVED_UTC = "2026-07-23T19:30:41Z"
RELEASE_COMMIT = "67b5da876dd6a76b8b021d5a04d1c81ba79a4c50"
RELEASE_ROOT = (
    "https://raw.githubusercontent.com/cp2k/cp2k/"
    f"{RELEASE_COMMIT}/"
)
RELEASE_OBJECTS = {
    "docs/conf.py": {
        "sha256": "72e6f813af22aa7e65a01fb47ed4c8e11ce543e4245cf78b9b398302fbd6ee44",
        "bytes": 2286,
    },
    "docs/index.md": {
        "sha256": "4db714dfed217ac7fc613e70913e9f940f72427dc2ecd2a4867d1830b6b37411",
        "bytes": 1227,
    },
    "LICENSE": {
        "sha256": "8177f97513213526df2cf6184d8ff986c675afb514d4e68a404010521b880643",
        "bytes": 18092,
    },
}
OUTPUTS = {
    "manual": REFERENCES / "source-pack-cp2k-manual.json",
    "release": REFERENCES / "source-pack-cp2k-release.json",
    "scope": REFERENCES / "source-pack-scope-catalog.json",
    "seed": REFERENCES / "source-pack-seed.json",
    "proposal": REFERENCES / "source-pack-authority-consumer-proposal.json",
}


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON root must be an object")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def safe_fragment(value: str, *, maximum: int = 100) -> str:
    fragment = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return (fragment or "item")[:maximum].rstrip("-")


def semantic_id(prefix: str, value: str) -> str:
    return f"{prefix}.{safe_fragment(value)}.{sha256_text(value)[:10]}"


def source_id(source_path: str) -> str:
    """Return the canonical CP2K manual identity required by the validator."""

    return source_path.lower().replace("/", ".")


def origin_ref(relative_path: str) -> dict[str, str]:
    path = REPO_ROOT / relative_path
    return {"path": relative_path, "sha256": sha256_file(path)}


def external_source(
    *,
    identity: str,
    title: str,
    source_kind: str,
    locator: str,
    raw_sha256: str,
    raw_bytes: int,
    evidence_sha256: str,
    subject_ids: Iterable[str],
) -> dict[str, Any]:
    receipt = {
        "retrieval_method": "https-get",
        "retrieved_utc": RETRIEVED_UTC,
        "raw_sha256": raw_sha256,
        "raw_bytes": raw_bytes,
        "selected_sha256": raw_sha256,
        "selected_bytes": raw_bytes,
    }
    return {
        "source_id": identity,
        "title": title,
        "source_kind": source_kind,
        "locator": locator,
        "disposition": "included",
        "external_identity": {
            "kind": "external-receipt",
            "value": f"sha256:{raw_sha256}",
            "raw_sha256": raw_sha256,
            "raw_bytes": raw_bytes,
            "retrieved_utc": RETRIEVED_UTC,
            "evidence_sha256": evidence_sha256,
        },
        "slices": [
            {
                "slice_id": f"{identity}.whole",
                "order": 0,
                "title": f"Exact raw bytes of {title}",
                "selector": {
                    "layer": "raw-source",
                    "kind": "whole-source",
                    "value": "*",
                },
                "external_receipt": receipt,
                "subject_ids": sorted(set(subject_ids)),
                "loss_ids": [],
            }
        ],
    }


def provider_subject(
    subject_id: str,
    title: str,
    category: str,
    strength: str = "supporting",
) -> dict[str, str]:
    return {
        "subject_id": subject_id,
        "title": title,
        "category": category,
        "requirement_strength": strength,
        "evidence_class": "official-provider-required",
    }


def scope_subject(
    *,
    subject_id: str,
    subject_kind: str,
    evidence_class: str,
    origins: Iterable[dict[str, str]],
    statement: str,
    provider_input_ids: Iterable[str] = (),
    expected_disposition: str | None = None,
) -> dict[str, Any]:
    providers = sorted(set(provider_input_ids))
    if expected_disposition is None:
        expected_disposition = (
            "covered" if evidence_class == "official-provider-required"
            else "not-applicable"
        )
    unique_origins = {
        (item["path"], item["sha256"]): item for item in origins
    }
    return {
        "subject_id": subject_id,
        "subject_kind": subject_kind,
        "evidence_class": evidence_class,
        "origin_refs": [
            unique_origins[key] for key in sorted(unique_origins)
        ],
        "statement": statement,
        "expected_disposition": expected_disposition,
        "provider_input_ids": providers,
    }


def build_catalogs() -> dict[str, dict[str, Any]]:
    registry_path = REFERENCES / "official-source-registry.json"
    task_path = REFERENCES / "task-evidence-profiles.json"
    method_path = REFERENCES / "method-evidence-profiles.json"
    index_path = REFERENCES / "official-manual" / "index.json"
    manifest_path = REFERENCES / "official-manual" / "manifest.json"
    registry = load_json(registry_path)
    tasks = load_json(task_path)
    methods = load_json(method_path)
    index = load_json(index_path)
    manifest = load_json(manifest_path)

    topics = registry["topics"]
    pages = manifest["pages"]
    if len(index["pages"]) != 2946 or index["page_count"] != 2946:
        raise ValueError("CP2K manual discovery universe must contain 2946 pages")
    if len(topics) != 86 or len(pages) != 86:
        raise ValueError("CP2K curated manual inventory must contain 86 topics")
    if set(topics) != set(pages):
        raise ValueError("CP2K registry topics and mirror manifest disagree")

    registry_origin = origin_ref(
        f"skills/{SKILL_ID}/references/official-source-registry.json"
    )
    task_origin = origin_ref(
        f"skills/{SKILL_ID}/references/task-evidence-profiles.json"
    )
    method_origin = origin_ref(
        f"skills/{SKILL_ID}/references/method-evidence-profiles.json"
    )
    script_origin = origin_ref(
        f"skills/{SKILL_ID}/scripts/sync_source_pack_catalog.py"
    )

    provider_subjects: dict[str, dict[str, str]] = {}
    scope_subjects: dict[str, dict[str, Any]] = {}
    attachments: dict[str, set[str]] = defaultdict(set)

    def add_official(
        *,
        subject_id: str,
        title: str,
        category: str,
        subject_kind: str,
        origins: Iterable[dict[str, str]],
        statement: str,
        topic_names: Iterable[str],
        strength: str = "supporting",
    ) -> None:
        provider_subjects[subject_id] = provider_subject(
            subject_id, title, category, strength
        )
        scope_subjects[subject_id] = scope_subject(
            subject_id=subject_id,
            subject_kind=subject_kind,
            evidence_class="official-provider-required",
            origins=origins,
            statement=statement,
            provider_input_ids=("cp2k-manual",),
        )
        for topic_name in topic_names:
            if topic_name not in topics:
                raise ValueError(
                    f"official subject {subject_id} names unknown topic {topic_name}"
                )
            attachments[topic_name].add(subject_id)

    for topic_name in sorted(topics):
        sid = f"cp2k.topic.{topic_name}"
        add_official(
            subject_id=sid,
            title=f"CP2K manual topic: {topic_name}",
            category="provenance",
            subject_kind="documented-claim",
            origins=(registry_origin,),
            statement=(
                f"The Skill routes the semantic topic {topic_name!r} to the "
                "pinned CP2K 2026.2 manual page."
            ),
            topic_names=(topic_name,),
            strength="required",
        )

    quickstep_base = set(tasks.get("quickstep_base_source_topics", []))
    for task_name, profile in sorted(tasks["profiles"].items()):
        task_topics = set(profile.get("required_source_topics", []))
        if profile.get("claim_supported"):
            task_topics.update(quickstep_base)
        sid = f"cp2k.task.{task_name}"
        add_official(
            subject_id=sid,
            title=f"CP2K task profile: {task_name}",
            category="workflow",
            subject_kind="task",
            origins=(task_origin,),
            statement=(
                f"The {task_name} task profile requires version-matched CP2K "
                "manual evidence for its declared source topics."
            ),
            topic_names=task_topics,
            strength="required",
        )

    for method_name, profile in sorted(methods["profiles"].items()):
        sid = f"cp2k.method.{method_name}"
        add_official(
            subject_id=sid,
            title=f"CP2K method profile: {method_name}",
            category="workflow",
            subject_kind="capability",
            origins=(method_origin,),
            statement=(
                f"The {method_name} method profile is bounded by its pinned "
                "CP2K manual source topics."
            ),
            topic_names=profile["source_topics"],
            strength="required",
        )

    section_origins: dict[str, set[str]] = defaultdict(set)
    for profile in tasks["profiles"].values():
        for field in ("required_sections", "required_sections_any"):
            for section in profile.get(field, []):
                section_origins[section].add("task")
        for section in profile.get("run_type_sections", {}).values():
            section_origins[section].add("task")
    for profile in methods["profiles"].values():
        for section in profile.get("sections", []):
            section_origins[section].add("method")
    path_to_topic = {
        value["path"].casefold(): name for name, value in topics.items()
    }
    for section, origin_types in sorted(section_origins.items()):
        manual_path = f"CP2K_INPUT/{section}.html".casefold()
        topic_name = path_to_topic.get(manual_path)
        if topic_name is None:
            raise ValueError(f"no curated CP2K topic for section {section}")
        sid = semantic_id("cp2k.input-section", section)
        origins = []
        if "task" in origin_types:
            origins.append(task_origin)
        if "method" in origin_types:
            origins.append(method_origin)
        add_official(
            subject_id=sid,
            title=f"CP2K input section: {section}",
            category="input-parameter",
            subject_kind="input-keyword",
            origins=origins,
            statement=(
                f"Profiles explicitly require or detect the CP2K input "
                f"section {section}."
            ),
            topic_names=(topic_name,),
            strength="required",
        )

    explicit_keywords = sorted(
        {
            keyword
            for profile in tasks["profiles"].values()
            for keyword in profile.get("required_keywords", [])
        }
    )
    for keyword in explicit_keywords:
        section = keyword.split(":", 1)[0]
        topic_name = path_to_topic.get(
            f"CP2K_INPUT/{section}.html".casefold()
        )
        if topic_name is None:
            raise ValueError(f"no curated CP2K topic for keyword {keyword}")
        sid = semantic_id("cp2k.input-keyword", keyword)
        add_official(
            subject_id=sid,
            title=f"CP2K input keyword: {keyword}",
            category="input-parameter",
            subject_kind="input-keyword",
            origins=(task_origin,),
            statement=f"The MD profile explicitly requires {keyword}.",
            topic_names=(topic_name,),
            strength="required",
        )

    run_types = sorted(
        {
            run_type
            for profile in tasks["profiles"].values()
            for run_type in profile.get("run_types", [])
        }
    )
    for run_type in run_types:
        sid = semantic_id("cp2k.run-type", run_type)
        add_official(
            subject_id=sid,
            title=f"CP2K RUN_TYPE value: {run_type}",
            category="input-parameter",
            subject_kind="input-keyword",
            origins=(task_origin,),
            statement=(
                f"A task profile accepts the official CP2K RUN_TYPE value "
                f"{run_type}."
            ),
            topic_names=("global",),
            strength="required",
        )

    scientific_checks = set(tasks.get("common_claim_checks", []))
    scientific_dimensions: set[str] = set()
    evidence_roles: set[str] = set()
    maturity_values: set[str] = set()
    for profile in tasks["profiles"].values():
        scientific_checks.update(profile.get("required_claim_checks", []))
        scientific_dimensions.update(profile.get("scientific_dimensions", []))
        evidence_roles.update(profile.get("required_run_evidence_roles", []))
        maturity_values.add(profile["run_audit_maturity"])
    for profile in methods["profiles"].values():
        maturity_values.add(profile["maturity"])

    for check in sorted(scientific_checks):
        sid = semantic_id("cp2k.scientific-check", check)
        scope_subjects[sid] = scope_subject(
            subject_id=sid,
            subject_kind="claim",
            evidence_class="scientific-methodology",
            origins=(task_origin,),
            statement=(
                f"Scientific acceptance requires the local methodology check "
                f"{check}; an official manual page cannot satisfy it alone."
            ),
        )
    for dimension in sorted(scientific_dimensions):
        sid = semantic_id("cp2k.scientific-dimension", dimension)
        scope_subjects[sid] = scope_subject(
            subject_id=sid,
            subject_kind="limitation",
            evidence_class="scientific-methodology",
            origins=(task_origin,),
            statement=(
                f"The convergence or validity dimension {dimension} remains "
                "a case-specific scientific evidence obligation."
            ),
        )
    for role in sorted(evidence_roles):
        sid = semantic_id("cp2k.evidence-role", role)
        scope_subjects[sid] = scope_subject(
            subject_id=sid,
            subject_kind="output-field",
            evidence_class="deterministic-tool-behavior",
            origins=(task_origin,),
            statement=(
                f"The local audit profile deterministically requests the "
                f"evidence role {role}."
            ),
        )
    for maturity in sorted(maturity_values):
        sid = semantic_id("cp2k.maturity", maturity)
        scope_subjects[sid] = scope_subject(
            subject_id=sid,
            subject_kind="limitation",
            evidence_class="repository-policy",
            origins=(task_origin, method_origin),
            statement=(
                f"The repository-local maturity label {maturity} limits "
                "automation claims and is not an upstream CP2K statement."
            ),
        )

    release_subjects = {
        "cp2k.release.docs-configuration": provider_subject(
            "cp2k.release.docs-configuration",
            "CP2K exact-release documentation configuration",
            "provenance",
            "informational",
        ),
        "cp2k.release.docs-entrypoint": provider_subject(
            "cp2k.release.docs-entrypoint",
            "CP2K exact-release documentation entrypoint",
            "provenance",
            "informational",
        ),
    }
    for sid, title in (
        (
            "cp2k.release.docs-configuration",
            "The exact CP2K release contains the pinned documentation build "
            "configuration, retained only as external metadata.",
        ),
        (
            "cp2k.release.docs-entrypoint",
            "The exact CP2K release contains the pinned documentation "
            "entrypoint, retained only as external metadata.",
        ),
    ):
        scope_subjects[sid] = scope_subject(
            subject_id=sid,
            subject_kind="documented-claim",
            evidence_class="official-provider-required",
            origins=(script_origin,),
            statement=title,
            provider_input_ids=("cp2k-release",),
        )

    manifest_sha = sha256_file(manifest_path)
    manual_sources = []
    for topic_name in sorted(pages):
        page = pages[topic_name]
        identity = source_id(page["source_path"])
        manual_sources.append(
            external_source(
                identity=identity,
                title=f"CP2K 2026.2 manual: {page['source_path']}",
                source_kind=(
                    "reference-page"
                    if page["source_path"].startswith("CP2K_INPUT")
                    else "guide"
                ),
                locator=page["source_url"],
                raw_sha256=page["raw_sha256"],
                raw_bytes=page["raw_bytes"],
                evidence_sha256=manifest_sha,
                subject_ids=attachments[topic_name],
            )
        )

    discovered_paths = set(index["pages"])
    included_paths = {page["source_path"] for page in pages.values()}
    missing_paths = sorted(discovered_paths - included_paths)
    if len(missing_paths) != 2860:
        raise ValueError(
            f"CP2K reviewed exclusion count must be 2860, got {len(missing_paths)}"
        )
    manual_root = registry["manual_root"].rstrip("/") + "/"
    exclusions = [
        {
            "source_id": source_id(path),
            "title": f"CP2K 2026.2 discovered page: {path}",
            "locator": manual_root + path,
            "reason_code": "other",
            "rationale": (
                "Discovered in the complete 2946-page manual index but not "
                "yet retrieved, byte-identified, semantically sliced, and "
                "reviewed for this metadata-only curated pack."
            ),
            "reviewed_utc": manifest["retrieved_utc"],
        }
        for path in missing_paths
    ]
    manual_catalog = {
        "schema_version": "1.0",
        "contract_name": "official-document-source-catalog",
        "version_scope": {
            "kind": "exact",
            "value": "2026.2",
            "retrieved_utc": manifest["retrieved_utc"],
            "snapshot_identity": {
                "kind": "manifest",
                "value": (
                    f"sha256:{sha256_file(index_path)};pages:"
                    f"{index['page_count']}"
                ),
                "content_sha256": sha256_file(index_path),
            },
        },
        "upstream_universe_complete": True,
        "inventory_locator": manual_root,
        "sources": sorted(manual_sources, key=lambda item: item["source_id"]),
        "subjects": [
            provider_subjects[key] for key in sorted(provider_subjects)
        ],
        "reviewed_exclusions": exclusions,
        "losses": [],
        "license": {
            "identity": {
                "identifier": None,
                "terms_urls": [],
                "verification": "unknown",
            },
            "assessment": "unresolved",
            "allowed_storage_modes": [
                "metadata-only",
                "external-runtime-only",
            ],
            "official_terms_locator": RELEASE_ROOT + "LICENSE",
            "limitations": [
                "The central CP2K manual authority has no verified "
                "documentation-license identity; no document body is stored."
            ],
        },
        "limitations": [
            "Only 86 of 2946 discovered manual pages have exact raw external "
            "receipts; all 2860 missing pages are enumerated exclusions.",
            "Raw HTML identities and local derived Markdown snapshot "
            "identities remain distinct and are never substituted.",
            "External whole-source selection receipts are not yet backed by a "
            "trusted platform attestation, so coverage remains partial.",
        ],
        "blockers": [],
    }

    release_docs = []
    for path, sid in (
        ("docs/conf.py", "cp2k.release.docs-configuration"),
        ("docs/index.md", "cp2k.release.docs-entrypoint"),
    ):
        receipt = RELEASE_OBJECTS[path]
        release_docs.append(
            external_source(
                identity=source_id(path),
                title=f"CP2K exact release source: {path}",
                source_kind="source-documentation",
                locator=RELEASE_ROOT + path,
                raw_sha256=receipt["sha256"],
                raw_bytes=receipt["bytes"],
                evidence_sha256=RELEASE_OBJECTS["LICENSE"]["sha256"],
                subject_ids=(sid,),
            )
        )
    aggregate = sha256_text(
        "".join(
            RELEASE_OBJECTS[path]["sha256"]
            for path in sorted(RELEASE_OBJECTS)
        )
    )
    release_catalog = {
        "schema_version": "1.0",
        "contract_name": "official-document-source-catalog",
        "version_scope": {
            "kind": "exact",
            "value": "2026.2",
            "retrieved_utc": RETRIEVED_UTC,
            "snapshot_identity": {
                "kind": "revision",
                "value": RELEASE_COMMIT,
                "content_sha256": aggregate,
            },
        },
        "upstream_universe_complete": False,
        "inventory_locator": RELEASE_ROOT + "docs/index.md",
        "sources": release_docs,
        "subjects": [
            release_subjects[key] for key in sorted(release_subjects)
        ],
        "reviewed_exclusions": [],
        "losses": [],
        "license": {
            "identity": {
                "identifier": None,
                "terms_urls": [],
                "verification": "unknown",
            },
            "assessment": "unresolved",
            "allowed_storage_modes": [
                "metadata-only",
                "external-runtime-only",
            ],
            "official_terms_locator": RELEASE_ROOT + "LICENSE",
            "limitations": [
                "The root CP2K LICENSE bytes are pinned, but the central "
                "authority keeps documentation-specific license scope "
                "unresolved."
            ],
        },
        "limitations": [
            "This bounded release-source corpus contains docs/conf.py and "
            "docs/index.md only; it is not a complete release documentation "
            "inventory.",
            "All upstream content remains external and metadata-only.",
        ],
        "blockers": [],
    }
    generated_catalog_origins = {
        "cp2k-manual": {
            "path": OUTPUTS["manual"].relative_to(REPO_ROOT).as_posix(),
            "sha256": sha256_bytes(canonical_json_bytes(manual_catalog)),
        },
        "cp2k-release": {
            "path": OUTPUTS["release"].relative_to(REPO_ROOT).as_posix(),
            "sha256": sha256_bytes(canonical_json_bytes(release_catalog)),
        },
    }
    for item in scope_subjects.values():
        retained = [
            origin
            for origin in item["origin_refs"]
            if "/official-" not in origin["path"]
        ]
        if len(retained) != len(item["origin_refs"]):
            retained.extend(
                generated_catalog_origins[provider_id]
                for provider_id in item["provider_input_ids"]
            )
        unique = {
            (origin["path"], origin["sha256"]): origin
            for origin in retained
        }
        item["origin_refs"] = [unique[key] for key in sorted(unique)]
    scope_catalog = {
        "schema_version": "1.0",
        "contract_name": "official-document-scope-catalog",
        "skill_id": SKILL_ID,
        "extractor_id": "cp2k-semantic-profile-v1",
        "subjects": [
            scope_subjects[key] for key in sorted(scope_subjects)
        ],
    }
    return {
        "manual": manual_catalog,
        "release": release_catalog,
        "scope": scope_catalog,
    }


def validate_catalogs(catalogs: dict[str, dict[str, Any]]) -> None:
    schemas = {
        "manual": REPO_ROOT
        / "contracts"
        / "official-document-source-catalog.schema.json",
        "release": REPO_ROOT
        / "contracts"
        / "official-document-source-catalog.schema.json",
        "scope": REPO_ROOT
        / "contracts"
        / "official-document-scope-catalog.schema.json",
    }
    for name, data in catalogs.items():
        schema = load_json(schemas[name])
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(
            schema, format_checker=FormatChecker()
        )
        errors = sorted(
            validator.iter_errors(data),
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
            raise ValueError(f"{name} catalog schema invalid: {rendered}")


def build_seed_and_proposal(
    catalogs: dict[str, dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, Any]]:
    def generated_ref(name: str) -> dict[str, str]:
        return {
            "path": OUTPUTS[name].relative_to(REPO_ROOT).as_posix(),
            "sha256": sha256_bytes(canonical_json_bytes(catalogs[name])),
        }

    providers = [
        {
            "input_id": "cp2k-manual",
            "adapter_id": "declarative-catalog-v1",
            "authority_id": "cp2k-official-manual",
            "provider_id": "cp2k",
            "source_ref": generated_ref("manual"),
        },
        {
            "input_id": "cp2k-release",
            "adapter_id": "declarative-catalog-v1",
            "authority_id": "cp2k-release-source-docs",
            "provider_id": "cp2k",
            "source_ref": generated_ref("release"),
        },
    ]
    seed = {
        "schema_version": "1.0",
        "contract_name": "official-document-pack-seed",
        "skill_id": SKILL_ID,
        "status_ceiling": "partial",
        "scope_extractor_id": "cp2k-semantic-profile-v1",
        "scope_catalog_ref": generated_ref("scope"),
        "providers": providers,
        "limitations": [
            "The CP2K manual pack includes exact raw receipts for only 86 of "
            "2946 discovered pages; all other pages remain reviewed exclusions.",
            "The exact-release source catalog is deliberately bounded and the "
            "central documentation license identity remains unresolved.",
            "External selector receipts and complete source-tree extraction "
            "have no trusted platform attestation, so this seed cannot claim "
            "complete coverage.",
        ],
        "blockers": [],
    }
    proposal = {
        "schema_version": "1.0",
        "contract_name": "official-document-authority-consumer-proposal",
        "proposal_status": "skill-local-non-authoritative",
        "skill_id": SKILL_ID,
        "consumer_path": f"skills/{SKILL_ID}",
        "providers": [
            {
                "input_id": provider["input_id"],
                "authority_id": provider["authority_id"],
                "provider_id": provider["provider_id"],
                "source_catalog_ref": provider["source_ref"],
                "consumer_binding": {
                    "binding_id": (
                        "cp2k-skill-cp2k-manual"
                        if provider["input_id"] == "cp2k-manual"
                        else "cp2k-skill-cp2k-release-source"
                    ),
                    "consumer_lifecycle": "active",
                    "purpose": "official-document-coverage",
                    "claim_ceiling": "registered-skill-scope",
                },
            }
            for provider in providers
        ],
        "limitations": [
            "This Skill-local proposal cannot create, widen, or override the "
            "canonical authority and consumer registries."
        ],
    }
    schema = load_json(
        REPO_ROOT / "contracts" / "official-document-pack-seed.schema.json"
    )
    validator = Draft202012Validator(
        schema, format_checker=FormatChecker()
    )
    errors = sorted(
        validator.iter_errors(seed),
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
        raise ValueError(f"seed schema invalid: {rendered}")
    return seed, proposal


def fetch_with_curl(url: str) -> bytes:
    command = [
        "curl",
        "--fail",
        "--silent",
        "--show-error",
        "--location",
        "--proto",
        "=https",
        "--tlsv1.2",
        "--retry",
        "3",
        "--connect-timeout",
        "20",
        "--max-time",
        "120",
        url,
    ]
    completed = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"HTTPS retrieval failed for {url}: {detail}")
    return completed.stdout


def refresh_external_identities(
    catalogs: dict[str, dict[str, Any]]
) -> None:
    expected: dict[str, tuple[str, int]] = {}
    for name in ("manual", "release"):
        for source in catalogs[name]["sources"]:
            identity = source["external_identity"]
            expected[source["locator"]] = (
                identity["raw_sha256"],
                identity["raw_bytes"],
            )
    expected[RELEASE_ROOT + "LICENSE"] = (
        RELEASE_OBJECTS["LICENSE"]["sha256"],
        RELEASE_OBJECTS["LICENSE"]["bytes"],
    )
    for index, url in enumerate(sorted(expected), start=1):
        wanted_hash, wanted_bytes = expected[url]
        raw = fetch_with_curl(url)
        actual_hash = hashlib.sha256(raw).hexdigest()
        if actual_hash != wanted_hash or len(raw) != wanted_bytes:
            raise ValueError(
                f"upstream identity mismatch for {url}: "
                f"sha256={actual_hash}, bytes={len(raw)}"
            )
        print(f"VERIFY {index}/{len(expected)} {url}", file=sys.stderr)


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def synchronize(*, check: bool, refresh: bool) -> int:
    catalogs = build_catalogs()
    validate_catalogs(catalogs)
    seed, proposal = build_seed_and_proposal(catalogs)
    outputs = {**catalogs, "seed": seed, "proposal": proposal}
    if refresh:
        refresh_external_identities(catalogs)
    stale: list[str] = []
    for name, output in OUTPUTS.items():
        payload = canonical_json_bytes(outputs[name])
        current = output.read_bytes() if output.is_file() else None
        if current == payload:
            continue
        stale.append(output.relative_to(REPO_ROOT).as_posix())
        if not check:
            atomic_write(output, payload)
    if check and stale:
        print(
            "ERROR: stale CP2K source-pack catalogs: " + ", ".join(stale),
            file=sys.stderr,
        )
        return 2
    verb = "checked" if check else "synchronized"
    print(
        f"PASS: {verb} CP2K metadata-only source-pack catalogs "
        f"(86 included, 2860 excluded manual pages)"
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="offline exact-byte comparison; never performs network access",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="verify every pinned external object over HTTPS without storing it",
    )
    args = parser.parse_args()
    if args.check and args.refresh:
        parser.error("--check is offline and cannot be combined with --refresh")
    return args


def main() -> int:
    args = parse_args()
    try:
        return synchronize(check=args.check, refresh=args.refresh)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
