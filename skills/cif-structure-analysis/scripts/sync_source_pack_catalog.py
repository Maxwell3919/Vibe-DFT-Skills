#!/usr/bin/env python3
"""Generate deterministic metadata-only official-document pack inputs."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable


SKILL_ID = "cif-structure-analysis"
EXTRACTOR_ID = "cif-structure-analysis-scope-v1"
RETRIEVED_UTC = "2026-07-24T00:00:00Z"


def repository_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if parent.joinpath("registry", "skill-registry.yaml").is_file():
            return parent
    raise RuntimeError("cannot locate repository root")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def safe_id(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._:-]+", "-", value.strip()).strip("-")
    if not normalized:
        raise ValueError(f"cannot derive safe id from {value!r}")
    return normalized


def origin(root: Path, relative: str) -> dict[str, str]:
    return {"path": relative, "sha256": sha256_file(root / relative)}


def heading_subjects(root: Path) -> list[dict[str, Any]]:
    relative_paths = [
        f"skills/{SKILL_ID}/SKILL.md",
        f"skills/{SKILL_ID}/references/dependencies-and-capabilities.md",
        f"skills/{SKILL_ID}/references/extension-interfaces.md",
        f"skills/{SKILL_ID}/references/structure-manifest.md",
    ]
    subjects: list[dict[str, Any]] = []
    for relative in relative_paths:
        path = root / relative
        source_ref = origin(root, relative)
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^(#{1,4})\s+(.+?)\s*$", line)
            if match is None:
                continue
            title = match.group(2)
            if match.group(1) == "#" and path.name == "SKILL.md":
                continue
            subjects.append(
                {
                    "subject_id": (
                        f"section:{safe_id(path.stem)}:{safe_id(title.lower())}"
                    ),
                    "subject_kind": (
                        "limitation"
                        if any(
                            token in title.lower()
                            for token in ("limit", "unsupported", "warning", "not")
                        )
                        else "workflow"
                    ),
                    "evidence_class": "repository-policy",
                    "origin_refs": [source_ref],
                    "statement": f"The Skill declares the section-level contract: {title}.",
                    "expected_disposition": "not-applicable",
                    "provider_input_ids": [],
                }
            )
    return subjects


def public_symbols(path: Path) -> tuple[tuple[str, str], ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    result: list[tuple[str, str]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name.startswith("_"):
                continue
            kind = "task" if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else "capability"
            result.append((node.name, kind))
    return tuple(sorted(result))


def tool_subjects(root: Path) -> list[dict[str, Any]]:
    script_root = root / "skills" / SKILL_ID / "scripts"
    paths = [
        script_root / "analyze_cif.py",
        *sorted((script_root / "ciftool").glob("*.py")),
    ]
    subjects: list[dict[str, Any]] = []
    for path in paths:
        relative = path.relative_to(root).as_posix()
        source_ref = origin(root, relative)
        module_id = safe_id(path.stem)
        for symbol, subject_kind in public_symbols(path):
            subjects.append(
                {
                    "subject_id": f"tool:{module_id}:{safe_id(symbol)}",
                    "subject_kind": subject_kind,
                    "evidence_class": "deterministic-tool-behavior",
                    "origin_refs": [source_ref],
                    "statement": (
                        f"The local {module_id} module implements the public "
                        f"{symbol} symbol."
                    ),
                    "expected_disposition": "not-applicable",
                    "provider_input_ids": [],
                }
            )
    return subjects


PROVIDER_SUBJECTS: tuple[tuple[str, str, str, str], ...] = (
    (
        "iucr:cif11-syntax",
        "documented-claim",
        "CIF 1.1 syntax defines the legacy document grammar consumed by the Skill.",
        "iucr-cif-standards",
    ),
    (
        "iucr:cif2-syntax",
        "documented-claim",
        "CIF 2.0 defines the magic header and extended syntax routed to the CIF2 parser.",
        "iucr-cif-standards",
    ),
    (
        "iucr:core-dictionary",
        "documented-claim",
        "The core CIF dictionary defines crystallographic data names used as metadata.",
        "iucr-cif-standards",
    ),
    (
        "ase:cif-materialization",
        "capability",
        "ASE materializes supported CIF structures as Atoms objects.",
        "ase-3-29",
    ),
    (
        "ase:periodic-neighbors",
        "capability",
        "ASE provides periodic neighbor-list and cutoff behavior used by the Skill.",
        "ase-3-29",
    ),
    (
        "ase:element-data",
        "capability",
        "ASE supplies element masses, radii, and color metadata used by the Skill.",
        "ase-3-29",
    ),
    (
        "gemmi:cif11-parser",
        "capability",
        "Gemmi parses CIF 1.1 documents and exposes block, tag, and loop structure.",
        "gemmi-0-7-5",
    ),
    (
        "gemmi:strict-check",
        "capability",
        "Gemmi strict checking is used as syntax evidence without CIF2 or DDLm support.",
        "gemmi-0-7-5",
    ),
    (
        "pycifrw:cif2-parser",
        "capability",
        "PyCifRW supplies the CIF2 parsing route used by the Skill.",
        "pycifrw-5-0-1",
    ),
    (
        "spglib:symmetry-dataset",
        "capability",
        "spglib supplies symmetry datasets, equivalent atoms, and Wyckoff evidence.",
        "spglib-2-7-0",
    ),
    (
        "spglib:standardization",
        "capability",
        "spglib supplies primitive and conventional-cell standardization.",
        "spglib-2-7-0",
    ),
)


def provider_scope_subjects(root: Path) -> list[dict[str, Any]]:
    refs = {
        "iucr-cif-standards": f"skills/{SKILL_ID}/references/structure-manifest.md",
        "ase-3-29": f"skills/{SKILL_ID}/references/dependencies-and-capabilities.md",
        "gemmi-0-7-5": f"skills/{SKILL_ID}/references/dependencies-and-capabilities.md",
        "pycifrw-5-0-1": f"skills/{SKILL_ID}/references/dependencies-and-capabilities.md",
        "spglib-2-7-0": f"skills/{SKILL_ID}/references/dependencies-and-capabilities.md",
    }
    result: list[dict[str, Any]] = []
    for subject_id, subject_kind, statement, input_id in PROVIDER_SUBJECTS:
        result.append(
            {
                "subject_id": subject_id,
                "subject_kind": subject_kind,
                "evidence_class": "official-provider-required",
                "origin_refs": [origin(root, refs[input_id])],
                "statement": statement,
                "expected_disposition": "partial",
                "provider_input_ids": [input_id],
            }
        )
    return result


def scope_catalog(root: Path) -> dict[str, Any]:
    subjects = heading_subjects(root) + tool_subjects(root) + provider_scope_subjects(root)
    subjects.sort(key=lambda item: item["subject_id"])
    ids = [item["subject_id"] for item in subjects]
    if len(ids) != len(set(ids)):
        raise ValueError("scope extractor produced duplicate subject ids")
    return {
        "schema_version": "1.0",
        "contract_name": "official-document-scope-catalog",
        "skill_id": SKILL_ID,
        "extractor_id": EXTRACTOR_ID,
        "subjects": subjects,
    }


def external_source(
    *,
    source_id: str,
    title: str,
    source_kind: str,
    locator: str,
    revision: str,
    sha256: str,
    size: int,
    subject_ids: Iterable[str],
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "title": title,
        "source_kind": source_kind,
        "locator": locator,
        "disposition": "included",
        "external_identity": {
            "kind": "revision",
            "value": revision,
            "raw_sha256": sha256,
            "raw_bytes": size,
            "retrieved_utc": RETRIEVED_UTC,
        },
        "slices": [
            {
                "slice_id": f"{source_id}:whole",
                "order": 0,
                "title": title,
                "selector": {
                    "layer": "raw-source",
                    "kind": "whole-source",
                    "value": "*",
                },
                "external_receipt": {
                    "retrieval_method": "https-get",
                    "retrieved_utc": RETRIEVED_UTC,
                    "raw_sha256": sha256,
                    "raw_bytes": size,
                    "selected_sha256": sha256,
                    "selected_bytes": size,
                },
                "subject_ids": sorted(set(subject_ids)),
                "loss_ids": [],
            }
        ],
    }


def subject_records(input_id: str) -> list[dict[str, str]]:
    result = []
    for subject_id, subject_kind, statement, selected_input in PROVIDER_SUBJECTS:
        if selected_input != input_id:
            continue
        result.append(
            {
                "subject_id": subject_id,
                "title": statement,
                "category": (
                    "validation-rule"
                    if subject_kind == "validation-rule"
                    else "workflow"
                    if subject_kind == "documented-claim"
                    else "other"
                ),
                "requirement_strength": "required",
                "evidence_class": "official-provider-required",
            }
        )
    return result


def catalog(
    *,
    input_id: str,
    version: str,
    inventory_locator: str,
    sources: list[dict[str, Any]],
    license_identifier: str | None,
    terms_url: str,
    license_assessment: str = "conditional",
    limitations: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "contract_name": "official-document-source-catalog",
        "version_scope": {
            "kind": "exact",
            "value": version,
            "retrieved_utc": None,
            "snapshot_identity": None,
        },
        "upstream_universe_complete": False,
        "inventory_locator": inventory_locator,
        "sources": sources,
        "subjects": subject_records(input_id),
        "reviewed_exclusions": [],
        "losses": [],
        "license": {
            "identity": {
                "identifier": license_identifier,
                "terms_urls": [terms_url],
                "verification": (
                    "unknown" if license_identifier is None else "unverified"
                ),
            },
            "assessment": license_assessment,
            "allowed_storage_modes": ["metadata-only", "external-runtime-only"],
            "official_terms_locator": terms_url,
            "limitations": [
                "Only metadata and external receipts are stored; official source text is not embedded."
            ],
        },
        "limitations": limitations,
        "blockers": [],
    }


def provider_catalogs() -> dict[str, dict[str, Any]]:
    iucr_api_revision = "1ddf445dc3dc82c211396b02e8af5bea3230a211"
    core_revision = "6b12b6782b66e57dd18b2f413e1c7bcde4d59907"
    ase_revision = "f27c0005ae6a67ea419f996e728668865bfc1f86"
    gemmi_revision = "5cc1c23c6007e0e6cbd69289c6f7c0bff50e943e"
    pycifrw_revision = "046dae8fead29d9f7c0b7df2544f943558b55b8b"
    spglib_revision = "12355c77fb7c505a55f52cae36341d73b781a065"
    return {
        "iucr-cif-standards": catalog(
            input_id="iucr-cif-standards",
            version="CIF-1.1+CIF-2.0+core-3.2.0",
            inventory_locator="https://github.com/COMCIFS",
            sources=[
                external_source(
                    source_id="comcifs-cif-api-readme",
                    title="COMCIFS CIF API reference overview",
                    source_kind="source-documentation",
                    locator=(
                        "https://raw.githubusercontent.com/COMCIFS/cif_api/"
                        f"{iucr_api_revision}/README.md"
                    ),
                    revision=iucr_api_revision,
                    sha256="325edc7382f19f640a095171df0bbd6a5e24afe0e1dc8656927f038350954ce4",
                    size=6265,
                    subject_ids=["iucr:cif11-syntax"],
                ),
                external_source(
                    source_id="comcifs-cif2-ebnf",
                    title="COMCIFS CIF2 EBNF",
                    source_kind="reference-page",
                    locator=(
                        "https://raw.githubusercontent.com/COMCIFS/cif_core/"
                        f"{core_revision}/CIF2-EBNF.txt"
                    ),
                    revision=core_revision,
                    sha256="8b309de8091391e9d36117567eafe1cb3c9ab7eaced59e0497bf0dd68e88485c",
                    size=12759,
                    subject_ids=["iucr:cif2-syntax"],
                ),
                external_source(
                    source_id="comcifs-core-dictionary-3-2-0",
                    title="COMCIFS core CIF dictionary 3.2.0",
                    source_kind="reference-page",
                    locator=(
                        "https://raw.githubusercontent.com/COMCIFS/cif_core/"
                        f"{core_revision}/cif_core.dic"
                    ),
                    revision=core_revision,
                    sha256="c1ec38fab9f505c2ce03838323e7cdea46585b16281961ae6762a2869ae03ecc",
                    size=839905,
                    subject_ids=["iucr:core-dictionary"],
                ),
            ],
            license_identifier=None,
            terms_url="https://www.iucr.org/resources/cif",
            license_assessment="unresolved",
            limitations=[
                "The formal IUCr portal could not be byte-bound by the offline-compatible fetch path.",
                "CIF dictionary redistribution terms remain unresolved.",
            ],
        ),
        "ase-3-29": catalog(
            input_id="ase-3-29",
            version="3.29.0",
            inventory_locator=f"https://gitlab.com/ase/ase/-/tree/{ase_revision}/doc",
            sources=[
                external_source(
                    source_id="ase-cif-io-doc",
                    title="ASE 3.29.0 I/O documentation",
                    source_kind="source-documentation",
                    locator=(
                        f"https://gitlab.com/ase/ase/-/raw/{ase_revision}/"
                        "doc/ase/io/io.rst"
                    ),
                    revision=ase_revision,
                    sha256="f9ff991bae9525683fefafa704205de934a88c3399d9912ae64bc26e930f2078",
                    size=5187,
                    subject_ids=["ase:cif-materialization"],
                ),
                external_source(
                    source_id="ase-neighborlist-doc",
                    title="ASE 3.29.0 neighbor-list documentation",
                    source_kind="source-documentation",
                    locator=(
                        f"https://gitlab.com/ase/ase/-/raw/{ase_revision}/"
                        "doc/ase/neighborlist.rst"
                    ),
                    revision=ase_revision,
                    sha256="5be1616b83f7648cf42c85aae346eb829ab13f09ad957245db96a07a0cf2b34d",
                    size=1368,
                    subject_ids=["ase:periodic-neighbors"],
                ),
                external_source(
                    source_id="ase-data-doc",
                    title="ASE 3.29.0 element-data documentation",
                    source_kind="source-documentation",
                    locator=(
                        f"https://gitlab.com/ase/ase/-/raw/{ase_revision}/"
                        "doc/ase/data.rst"
                    ),
                    revision=ase_revision,
                    sha256="2dd617677682521ce74be5bf1074e8a6ae9ce2d4423f921d59a481c5c44b842a",
                    size=7751,
                    subject_ids=["ase:element-data"],
                ),
            ],
            license_identifier="LGPL-2.1-or-later",
            terms_url=f"https://gitlab.com/ase/ase/-/raw/{ase_revision}/LICENSE",
            limitations=[
                "The Skill admits ASE versions older than this exact documentation snapshot."
            ],
        ),
        "gemmi-0-7-5": catalog(
            input_id="gemmi-0-7-5",
            version="0.7.5",
            inventory_locator=f"https://github.com/project-gemmi/gemmi/tree/{gemmi_revision}/docs",
            sources=[
                external_source(
                    source_id="gemmi-cif-doc",
                    title="Gemmi 0.7.5 CIF documentation",
                    source_kind="source-documentation",
                    locator=(
                        "https://raw.githubusercontent.com/project-gemmi/gemmi/"
                        f"{gemmi_revision}/docs/cif.rst"
                    ),
                    revision=gemmi_revision,
                    sha256="4f55da8227e66d3e2f8c1cc3a52324ccf6b5eb335c80159e330023894f1ebdd2",
                    size=84699,
                    subject_ids=["gemmi:cif11-parser", "gemmi:strict-check"],
                )
            ],
            license_identifier="MPL-2.0",
            terms_url=(
                "https://raw.githubusercontent.com/project-gemmi/gemmi/"
                f"{gemmi_revision}/LICENSE.txt"
            ),
            limitations=[
                "Gemmi documents CIF2 and DDLm as unsupported; those inputs are routed elsewhere."
            ],
        ),
        "pycifrw-5-0-1": catalog(
            input_id="pycifrw-5-0-1",
            version="5.0.1",
            inventory_locator=f"https://github.com/jamesrhester/pycifrw/tree/{pycifrw_revision}",
            sources=[
                external_source(
                    source_id="pycifrw-readme",
                    title="PyCifRW 5.0.1 README",
                    source_kind="source-documentation",
                    locator=(
                        "https://raw.githubusercontent.com/jamesrhester/pycifrw/"
                        f"{pycifrw_revision}/README.md"
                    ),
                    revision=pycifrw_revision,
                    sha256="25b03145b76075b30e6ce51dafb4f19ba8454f88246140071987ac934d2a7677",
                    size=3066,
                    subject_ids=["pycifrw:cif2-parser"],
                )
            ],
            license_identifier="LicenseRef-PyCifRW-Python-2.0-ANSTO",
            terms_url=(
                "https://raw.githubusercontent.com/jamesrhester/pycifrw/"
                f"{pycifrw_revision}/LICENSE"
            ),
            limitations=[
                "The compact docs directory is not the complete PyCifRW API and grammar universe."
            ],
        ),
        "spglib-2-7-0": catalog(
            input_id="spglib-2-7-0",
            version="2.7.0",
            inventory_locator=f"https://github.com/spglib/spglib/tree/{spglib_revision}/docs",
            sources=[
                external_source(
                    source_id="spglib-python-interface",
                    title="spglib 2.7.0 Python interface",
                    source_kind="source-documentation",
                    locator=(
                        "https://raw.githubusercontent.com/spglib/spglib/"
                        f"{spglib_revision}/docs/python-interface.md"
                    ),
                    revision=spglib_revision,
                    sha256="0d374f692d3afc212e685a612d2dc715942b80fa315e530cd42f6c851bd85807",
                    size=8995,
                    subject_ids=["spglib:symmetry-dataset"],
                ),
                external_source(
                    source_id="spglib-api",
                    title="spglib 2.7.0 API reference",
                    source_kind="source-documentation",
                    locator=(
                        "https://raw.githubusercontent.com/spglib/spglib/"
                        f"{spglib_revision}/docs/api.md"
                    ),
                    revision=spglib_revision,
                    sha256="47f5f6d07eb221b1309ac7b8daebbeae50ad6137cf5594ceb87c953b1b47255b",
                    size=25567,
                    subject_ids=["spglib:standardization"],
                ),
            ],
            license_identifier="BSD-3-Clause",
            terms_url=(
                "https://raw.githubusercontent.com/spglib/spglib/"
                f"{spglib_revision}/COPYING"
            ),
            limitations=[
                "The Skill admits spglib versions newer than this exact documentation snapshot."
            ],
        ),
    }


def consumer_binding(
    authority_id: str,
    provider_id: str,
    *,
    suffix: str,
) -> dict[str, Any]:
    return {
        "binding_id": f"{SKILL_ID}-{suffix}",
        "consumer_skill_id": SKILL_ID,
        "consumer_lifecycle": "active",
        "consumer_path": f"skills/{SKILL_ID}",
        "authority_id": authority_id,
        "provider_id": provider_id,
        "purpose": "official-document-coverage",
        "claim_ceiling": "registered-skill-scope",
    }


def proposed_authority(
    *,
    authority_id: str,
    display_name: str,
    provider_class: str,
    provider_id: str,
    exact_version: str,
    origins: list[str],
    path_prefixes: list[str],
    fact_urls: list[str],
    binding_suffix: str,
    limitation: str,
) -> dict[str, Any]:
    return {
        "authority_id": authority_id,
        "display_name": display_name,
        "proposed_lifecycle": "active",
        "provider_class": provider_class,
        "provider_id": provider_id,
        "allowed_https_origins": origins,
        "version_policy": {
            "allowed_scopes": ["exact"],
            "registered_scopes": [
                {
                    "scope": "exact",
                    "exact_version": exact_version,
                    "minimum_version": None,
                    "maximum_version": None,
                    "release_series": None,
                }
            ],
        },
        "content_policy": {
            "source_kinds": [
                "official-reference",
                "official-repository",
            ],
            "allowed_path_prefixes": path_prefixes,
            "query_policy": "forbidden",
            "fragment_policy": "forbidden",
            "resolution_mode": "platform-verified-only",
        },
        "content_identity_policy": {
            "mode": "platform-adapter-only",
            "unpinned_action": "adapter-required",
        },
        "canonical_snapshot": None,
        "license_policy": {
            "status": "unknown",
            "identifier": None,
            "terms_urls": [],
            "verification_status": "unresolved",
        },
        "redistribution_policy": {
            "allowed_values": ["unknown"],
            "bundle_content": "forbidden",
            "external_runtime_content": "platform-verification-required",
        },
        "limitations": [limitation],
        "provenance": {
            "verified_utc": RETRIEVED_UTC,
            "official_fact_urls": fact_urls,
        },
        "consumer_binding": consumer_binding(
            authority_id,
            provider_id,
            suffix=binding_suffix,
        ),
    }


def authority_proposal() -> dict[str, Any]:
    ase_revision = "f27c0005ae6a67ea419f996e728668865bfc1f86"
    gemmi_revision = "5cc1c23c6007e0e6cbd69289c6f7c0bff50e943e"
    pycifrw_revision = "046dae8fead29d9f7c0b7df2544f943558b55b8b"
    spglib_revision = "12355c77fb7c505a55f52cae36341d73b781a065"
    cif_api_revision = "1ddf445dc3dc82c211396b02e8af5bea3230a211"
    cif_core_revision = "6b12b6782b66e57dd18b2f413e1c7bcde4d59907"
    return {
        "schema_version": "1.0",
        "proposal_type": "official-source-authority-and-consumer-bindings",
        "skill_id": SKILL_ID,
        "lifecycle_effect": "none",
        "authorities": [
            proposed_authority(
                authority_id="iucr-comcifs-cif-standards",
                display_name="IUCr COMCIFS CIF standards sources",
                provider_class="standard",
                provider_id="iucr",
                exact_version="CIF-1.1+CIF-2.0+core-3.2.0",
                origins=["https://raw.githubusercontent.com"],
                path_prefixes=[
                    f"/COMCIFS/cif_api/{cif_api_revision}/",
                    f"/COMCIFS/cif_core/{cif_core_revision}/",
                ],
                fact_urls=[
                    (
                        "https://raw.githubusercontent.com/COMCIFS/cif_api/"
                        f"{cif_api_revision}/README.md"
                    ),
                    (
                        "https://raw.githubusercontent.com/COMCIFS/cif_core/"
                        f"{cif_core_revision}/CIF2-EBNF.txt"
                    ),
                ],
                binding_suffix="iucr-standards",
                limitation=(
                    "CIF grammar and dictionary source identity is exact, but "
                    "documentation licensing and the full IUCr portal universe "
                    "remain unresolved."
                ),
            ),
            proposed_authority(
                authority_id="ase-release-source-docs-3-29-0",
                display_name="ASE 3.29.0 release-source documentation",
                provider_class="software",
                provider_id="ase",
                exact_version="3.29.0",
                origins=["https://gitlab.com"],
                path_prefixes=[f"/ase/ase/-/raw/{ase_revision}/"],
                fact_urls=[
                    (
                        f"https://gitlab.com/ase/ase/-/raw/{ase_revision}/"
                        "doc/ase/io/io.rst"
                    )
                ],
                binding_suffix="ase-source",
                limitation=(
                    "This exact snapshot does not cover every ASE version "
                    "accepted by the Skill dependency range."
                ),
            ),
            proposed_authority(
                authority_id="gemmi-0-7-5-source-docs",
                display_name="Gemmi 0.7.5 release-source documentation",
                provider_class="software",
                provider_id="gemmi",
                exact_version="0.7.5",
                origins=["https://raw.githubusercontent.com"],
                path_prefixes=[
                    f"/project-gemmi/gemmi/{gemmi_revision}/"
                ],
                fact_urls=[
                    (
                        "https://raw.githubusercontent.com/project-gemmi/gemmi/"
                        f"{gemmi_revision}/docs/cif.rst"
                    )
                ],
                binding_suffix="gemmi-source",
                limitation=(
                    "Gemmi documents CIF2 and DDLm as unsupported; the Skill "
                    "must preserve its separate CIF2 route."
                ),
            ),
            proposed_authority(
                authority_id="pycifrw-5-0-1-source-docs",
                display_name="PyCifRW 5.0.1 release-source documentation",
                provider_class="software",
                provider_id="pycifrw",
                exact_version="5.0.1",
                origins=["https://raw.githubusercontent.com"],
                path_prefixes=[
                    f"/jamesrhester/pycifrw/{pycifrw_revision}/"
                ],
                fact_urls=[
                    (
                        "https://raw.githubusercontent.com/jamesrhester/pycifrw/"
                        f"{pycifrw_revision}/README.md"
                    )
                ],
                binding_suffix="pycifrw-source",
                limitation=(
                    "The selected README is not a complete PyCifRW API or "
                    "grammar corpus."
                ),
            ),
            proposed_authority(
                authority_id="spglib-release-source-docs-2-7-0",
                display_name="spglib 2.7.0 release-source documentation",
                provider_class="software",
                provider_id="spglib",
                exact_version="2.7.0",
                origins=["https://raw.githubusercontent.com"],
                path_prefixes=[f"/spglib/spglib/{spglib_revision}/"],
                fact_urls=[
                    (
                        "https://raw.githubusercontent.com/spglib/spglib/"
                        f"{spglib_revision}/docs/python-interface.md"
                    )
                ],
                binding_suffix="spglib-source",
                limitation=(
                    "This exact snapshot does not cover every spglib version "
                    "accepted by the Skill dependency range."
                ),
            ),
        ],
        "existing_authority_bindings": [],
        "provider_registry_proposals": [
            {
                "provider_class": "software",
                "provider_id": provider_id,
                "requested_state": "planned",
                "role": role,
                "intended_skill": SKILL_ID,
                "reason": (
                    "A software-class authority requires one canonical "
                    "software-registry provider identity."
                ),
            }
            for provider_id, role in (
                ("ase", "structure-library"),
                ("gemmi", "structure-library"),
                ("pycifrw", "structure-library"),
                ("spglib", "symmetry-library"),
            )
        ],
        "central_blockers": [
            "Create or review the four software provider identities before activating their software-class authorities.",
            "Add all five consumer bindings before running the production pack builder.",
            "Keep every new authority metadata-only until central license review resolves redistribution rights.",
        ],
        "invariants": [
            "No proposal changes Skill/software lifecycle, routing, installability, execution permission, or claim ceiling.",
            "Exact provider snapshots do not prove compatibility with the Skill's open-ended dependency ranges.",
        ],
    }


def build_outputs(root: Path) -> dict[Path, bytes]:
    skill_root = root / "skills" / SKILL_ID
    scope_path = skill_root / "references" / "source-pack-scope.json"
    outputs: dict[Path, bytes] = {
        scope_path: canonical_json_bytes(scope_catalog(root))
    }
    provider_specs = {
        "iucr-cif-standards": (
            "iucr-comcifs-cif-standards",
            "iucr",
        ),
        "ase-3-29": ("ase-release-source-docs-3-29-0", "ase"),
        "gemmi-0-7-5": ("gemmi-0-7-5-source-docs", "gemmi"),
        "pycifrw-5-0-1": ("pycifrw-5-0-1-source-docs", "pycifrw"),
        "spglib-2-7-0": (
            "spglib-release-source-docs-2-7-0",
            "spglib",
        ),
    }
    providers: list[dict[str, Any]] = []
    for input_id, value in sorted(provider_catalogs().items()):
        path = (
            skill_root / "references" / "source-pack-inputs" / f"{input_id}.json"
        )
        payload = canonical_json_bytes(value)
        outputs[path] = payload
        authority_id, provider_id = provider_specs[input_id]
        providers.append(
            {
                "input_id": input_id,
                "adapter_id": "declarative-catalog-v1",
                "authority_id": authority_id,
                "provider_id": provider_id,
                "source_ref": {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": sha256_bytes(payload),
                },
            }
        )
    seed = {
        "schema_version": "1.0",
        "contract_name": "official-document-pack-seed",
        "skill_id": SKILL_ID,
        "status_ceiling": "partial",
        "scope_extractor_id": "cif-structure-analysis-scope-v1",
        "scope_catalog_ref": {
            "path": scope_path.relative_to(root).as_posix(),
            "sha256": sha256_bytes(outputs[scope_path]),
        },
        "providers": providers,
        "limitations": [
            "The pack is metadata-only and does not embed official documentation text.",
            "Open-ended dependency ranges are not equivalent to these exact provider snapshots.",
            "IUCr dictionary licensing and full portal enumeration remain unresolved.",
        ],
        "blockers": [],
    }
    outputs[skill_root / "references" / "source-pack-seed.json"] = (
        canonical_json_bytes(seed)
    )
    outputs[
        skill_root / "references" / "source-pack-authority-proposal.json"
    ] = canonical_json_bytes(authority_proposal())
    return outputs


def sync(*, check: bool) -> tuple[str, ...]:
    root = repository_root()
    changed: list[str] = []
    for path, payload in sorted(
        build_outputs(root).items(), key=lambda item: item[0].as_posix()
    ):
        current = path.read_bytes() if path.is_file() else None
        if current == payload:
            continue
        changed.append(path.relative_to(root).as_posix())
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
    if check and changed:
        raise ValueError("stale source-pack inputs: " + ", ".join(changed))
    return tuple(changed)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        changed = sync(check=args.check)
    except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}")
        return 2
    verb = "checked" if args.check else "updated"
    print(f"PASS: {verb} {SKILL_ID} source-pack inputs ({len(changed)} changed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
