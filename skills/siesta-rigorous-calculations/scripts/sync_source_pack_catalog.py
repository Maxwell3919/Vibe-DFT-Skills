#!/usr/bin/env python3
"""Build policy-free v1.1 SIESTA portal and release-source catalogs.

The default mode writes deterministic catalogs. ``--check`` is offline and
compares exact bytes. ``--refresh`` re-fetches every pinned technical source
over HTTPS, verifies its hash and byte count, and discards the body.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import copy
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

from siesta_fdf_labels import matches_official_label


SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[3]
TOOLS_ROOT = REPO_ROOT / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from migrate_official_document_catalogs_v11 import (  # noqa: E402
    canonical_json_bytes as canonical_v11_json_bytes,
    convert_catalog_v10_to_v11,
)

REFERENCES = SKILL_ROOT / "references"
SKILL_ID = "siesta-rigorous-calculations"
RETRIEVED_UTC = "2026-07-23T19:30:41Z"
RELEASE_COMMIT = "e486d12067b96ff688179f0496d0ec21b6fae0ab"
RELEASE_ROOT = (
    "https://gitlab.com/siesta-project/siesta/-/raw/"
    f"{RELEASE_COMMIT}/"
)
RELEASE_LICENSE_URL = RELEASE_ROOT + "COPYING"
RELEASE_LICENSE = {
    "sha256": "fc82ca8b6fdb18d4e3e85cfd8ab58d1bcd3f1b29abe782895abd91d64763f8e7",
    "bytes": 35068,
}
PORTAL_REFERENCE_URL = (
    "https://docs.siesta-project.org/projects/siesta/en/5.4/reference/"
    "siesta.html"
)
PORTAL_PERFORMANCE_URL = (
    "https://docs.siesta-project.org/projects/siesta/en/5.4/reference/"
    "performance-options/"
)
PORTAL_LICENSE_URL = (
    "https://gitlab.com/siesta-project/documentation/siesta-docs/-/raw/"
    "ca6da4c46538bccce34776cdbb075fa4bfc2c6dc/LICENSE"
)
PORTAL_OBJECTS = {
    PORTAL_REFERENCE_URL: {
        "sha256": "b2228ffca6ec8a505bab4fcd8caaf9354add02f36fde3fb3d827087f4021926f",
        "bytes": 1155549,
    },
    PORTAL_PERFORMANCE_URL: {
        "sha256": "41da120fcff558729c51aa13053136e2d94eaf7ba829166907c58e959dc73957",
        "bytes": 18944,
    },
    PORTAL_LICENSE_URL: {
        "sha256": "7074fb66818fbbc771e52bb25b0273a586a4ed42bf21c923b7e880cf1a9597e9",
        "bytes": 20851,
    },
}

# These byte counts were verified against exact raw URLs at RELEASE_COMMIT.
# Hashes and URLs remain sourced from official-fdf-index.json and
# official-source-supplements.json so this table cannot replace either
# authority record.
RELEASE_SOURCE_BYTES = {
    "Docs/tex/sections/DFT+U.tex": 7270,
    "Docs/tex/sections/External_control.tex": 9007,
    "Docs/tex/sections/Options/Auxiliary_force_field.tex": 2870,
    "Docs/tex/sections/Options/Band_structure_analysis.tex": 5141,
    "Docs/tex/sections/Options/Basis_set_and_KB_projectors.tex": 62821,
    "Docs/tex/sections/Options/CheSS.tex": 2646,
    "Docs/tex/sections/Options/Chemical_analysis.tex": 15176,
    "Docs/tex/sections/Options/Density_of_states.tex": 8033,
    "Docs/tex/sections/Options/ELSI.tex": 6669,
    "Docs/tex/sections/Options/Efficiency.tex": 884,
    "Docs/tex/sections/Options/Electronic_structure.tex": 33761,
    "Docs/tex/sections/Options/General_system_descriptors.tex": 7191,
    "Docs/tex/sections/Options/GrimmeD3.tex": 5022,
    "Docs/tex/sections/Options/HS_matrix_elements.tex": 4891,
    "Docs/tex/sections/Options/K_point_sampling.tex": 6211,
    "Docs/tex/sections/Options/Macroscopic_polarization.tex": 6983,
    "Docs/tex/sections/Options/Netcharge_dipole_Efield.tex": 19527,
    "Docs/tex/sections/Options/Optical.tex": 3940,
    "Docs/tex/sections/Options/Output_cdf.tex": 2105,
    "Docs/tex/sections/Options/Output_charge_density_potential.tex": 9403,
    "Docs/tex/sections/Options/Output_denchar.tex": 769,
    "Docs/tex/sections/Options/PEXSI.tex": 20557,
    "Docs/tex/sections/Options/Parallel.tex": 4094,
    "Docs/tex/sections/Options/Real_space_grid.tex": 11045,
    "Docs/tex/sections/Options/Resource_accounting.tex": 3701,
    "Docs/tex/sections/Options/SCF_loop.tex": 64081,
    "Docs/tex/sections/Options/SOC.tex": 7227,
    "Docs/tex/sections/Options/Selected_wavefunctions.tex": 3335,
    "Docs/tex/sections/Options/Spin_polarization.tex": 4053,
    "Docs/tex/sections/Options/Structural_information.tex": 27212,
    "Docs/tex/sections/Options/UseSaveData.tex": 437,
    "Docs/tex/sections/Options/Wannier_Functions.tex": 24359,
    "Docs/tex/sections/Options/XC_functionals.tex": 7957,
    "Docs/tex/sections/Output.tex": 3654,
    "Docs/tex/sections/QMMM.tex": 13474,
    "Docs/tex/sections/RT-TDDFT.tex": 6192,
    "Docs/tex/sections/Relaxation_phonons_md.tex": 7905,
    "Docs/tex/sections/Relaxation_phonons_md/Constraints.tex": 8799,
    "Docs/tex/sections/Relaxation_phonons_md/Molecular_dynamics.tex": 4134,
    "Docs/tex/sections/Relaxation_phonons_md/Output.tex": 3712,
    "Docs/tex/sections/Relaxation_phonons_md/Phonons.tex": 2638,
    "Docs/tex/sections/Relaxation_phonons_md/Structural_relaxation.tex": 10424,
    "Docs/tex/sections/Relaxation_phonons_md/Target_stress.tex": 2794,
    "Docs/tex/sections/TranSIESTA/Kpoint_sampling.tex": 36804,
    "Docs/tex/sections/TranSIESTA/Options.tex": 22281,
    "Docs/tex/sections/Utils/lindhard.tex": 2251,
    "Docs/tex/sections/XML_output.tex": 2307,
    "Src/read_options.F90": 76916,
    "Src/scfconvergence_test.F": 7141,
    "Src/siesta_analysis.F90": 24453,
    "Src/siesta_end.F": 8743,
    "Src/siesta_forces.F90": 32479,
    "Src/write_subs.F": 41903,
}
OUTPUTS = {
    "portal": REFERENCES / "source-pack-siesta-portal.json",
    "release": REFERENCES / "source-pack-siesta-release.json",
    "scope": REFERENCES / "source-pack-scope-catalog.json",
    "seed": REFERENCES / "source-pack-seed.json",
    "proposal": REFERENCES / "source-pack-authority-consumer-proposal.json",
}


def canonical_json_bytes(value: Any) -> bytes:
    """Return the frozen pretty JSON used by the v1.0 migration preimage."""

    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def output_json_bytes(name: str, value: Any) -> bytes:
    """Serialize checked-in v1.1 inputs transactionally and deterministically."""

    if name == "proposal":
        # The local proposal is not a migrated production input and retains its
        # established human-readable serialization.
        return canonical_json_bytes(value)
    return canonical_v11_json_bytes(value)


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


def safe_fragment(value: str, *, maximum: int = 90) -> str:
    fragment = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return (fragment or "item")[:maximum].rstrip("-")


def semantic_id(prefix: str, value: str) -> str:
    return f"{prefix}.{safe_fragment(value)}.{sha256_text(value)[:12]}"


def release_source_id(path: str) -> str:
    """Return a path-preserving, collision-safe source identity."""

    return semantic_id("siesta.release", path)


def portal_source_id(url: str) -> str:
    return semantic_id("siesta.portal", url)


def origin_ref(relative_path: str) -> dict[str, str]:
    path = REPO_ROOT / relative_path
    return {"path": relative_path, "sha256": sha256_file(path)}


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
                "external_receipt": {
                    "retrieval_method": "https-get",
                    "retrieved_utc": RETRIEVED_UTC,
                    "raw_sha256": raw_sha256,
                    "raw_bytes": raw_bytes,
                    "selected_sha256": raw_sha256,
                    "selected_bytes": raw_bytes,
                },
                "subject_ids": sorted(set(subject_ids)),
                "loss_ids": [],
            }
        ],
    }


def profile_labels(tasks: dict[str, Any]) -> set[str]:
    labels = set(tasks["common"]["automated_labels"])
    for profile in tasks["profiles"].values():
        labels.update(profile.get("extra_automated_labels", []))
        labels.update(profile.get("required_input_all", []))
        for group in profile.get("required_input_any", []):
            labels.update(group)
    return labels


def _build_legacy_catalogs() -> dict[str, dict[str, Any]]:
    registry_path = REFERENCES / "official-source-registry.json"
    index_path = REFERENCES / "official-fdf-index.json"
    supplement_path = REFERENCES / "official-source-supplements.json"
    task_path = REFERENCES / "task-evidence-profiles.json"
    registry = load_json(registry_path)
    index = load_json(index_path)
    supplements = load_json(supplement_path)
    tasks = load_json(task_path)

    if (
        index["entry_count"] != 572
        or len(index["entries"]) != 572
        or len(index["source_files"]) != 47
    ):
        raise ValueError("SIESTA FDF inventory must contain 572 entries/47 files")
    supplement_files = {
        item["source_file"] for item in supplements["records"]
    }
    if len(supplements["records"]) != 9 or len(supplement_files) != 6:
        raise ValueError("SIESTA supplement inventory must contain 9 records/6 files")
    release_paths = {
        item["path"] for item in index["source_files"]
    } | supplement_files
    if release_paths != set(RELEASE_SOURCE_BYTES):
        raise ValueError("SIESTA raw-byte receipt paths do not match 47+6 inventory")

    registry_origin = origin_ref(
        f"skills/{SKILL_ID}/references/official-source-registry.json"
    )
    index_origin = origin_ref(
        f"skills/{SKILL_ID}/references/official-fdf-index.json"
    )
    supplement_origin = origin_ref(
        f"skills/{SKILL_ID}/references/official-source-supplements.json"
    )
    task_origin = origin_ref(
        f"skills/{SKILL_ID}/references/task-evidence-profiles.json"
    )
    script_origin = origin_ref(
        f"skills/{SKILL_ID}/scripts/sync_source_pack_catalog.py"
    )

    scope_subjects: dict[str, dict[str, Any]] = {}
    release_subjects: dict[str, dict[str, str]] = {}
    release_attachments: dict[str, set[str]] = defaultdict(set)
    entry_subject_by_location: dict[tuple[str, int], str] = {}

    def add_release_subject(
        *,
        subject_id: str,
        title: str,
        category: str,
        subject_kind: str,
        origin: dict[str, str],
        statement: str,
        paths: Iterable[str],
        strength: str = "supporting",
    ) -> None:
        release_subjects[subject_id] = provider_subject(
            subject_id, title, category, strength
        )
        scope_subjects[subject_id] = scope_subject(
            subject_id=subject_id,
            subject_kind=subject_kind,
            evidence_class="official-provider-required",
            origins=(origin,),
            statement=statement,
            provider_input_ids=("siesta-release",),
        )
        for path in paths:
            if path not in release_paths:
                raise ValueError(f"unknown SIESTA release source path {path}")
            release_attachments[path].add(subject_id)

    for entry in index["entries"]:
        identity_text = (
            f"{entry['label']}|{entry['source_file']}|{entry['source_line']}"
        )
        sid = semantic_id("siesta.fdf", identity_text)
        key = (entry["source_file"], entry["source_line"])
        if key in entry_subject_by_location:
            raise ValueError(f"duplicate SIESTA FDF source location {key}")
        entry_subject_by_location[key] = sid
        add_release_subject(
            subject_id=sid,
            title=(
                f"SIESTA FDF label {entry['label']} at "
                f"{entry['source_file']}:{entry['source_line']}"
            ),
            category="input-parameter",
            subject_kind="input-keyword",
            origin=index_origin,
            statement=(
                f"The exact 5.4.2 source documents the FDF label "
                f"{entry['label']} at a collision-safe source location."
            ),
            paths=(entry["source_file"],),
            strength="required",
        )

    output_marker_subjects: dict[str, str] = {}
    for record in supplements["records"]:
        identity_text = (
            f"{record['kind']}|{record['label']}|{record['source_file']}|"
            f"{record['source_line']}"
        )
        prefix = (
            "siesta.supplement.fdf"
            if record["kind"] == "fdf-source-definition"
            else "siesta.output-marker"
        )
        sid = semantic_id(prefix, identity_text)
        is_fdf = record["kind"] == "fdf-source-definition"
        add_release_subject(
            subject_id=sid,
            title=(
                f"SIESTA released-source {'FDF label' if is_fdf else 'output marker'}: "
                f"{record['label']}"
            ),
            category="input-parameter" if is_fdf else "output-observable",
            subject_kind="input-keyword" if is_fdf else "output-field",
            origin=supplement_origin,
            statement=(
                f"The exact released source records {record['label']} at "
                f"{record['source_file']}:{record['source_line']}."
            ),
            paths=(record["source_file"],),
            strength="required",
        )
        if not is_fdf:
            output_marker_subjects[record["label"]] = sid

    manual_entries = index["entries"]
    supplement_fdf = [
        record
        for record in supplements["records"]
        if record["kind"] == "fdf-source-definition"
    ]
    for label in sorted(profile_labels(tasks), key=str.casefold):
        matches = [
            entry
            for entry in manual_entries
            if matches_official_label(label, entry["label"])
        ]
        matches.extend(
            record
            for record in supplement_fdf
            if matches_official_label(label, record["label"])
        )
        if not matches:
            raise ValueError(
                f"task profile label has no exact official source: {label}"
            )
        sid = semantic_id("siesta.profile-keyword", label)
        add_release_subject(
            subject_id=sid,
            title=f"SIESTA task-profile FDF label: {label}",
            category="input-parameter",
            subject_kind="input-keyword",
            origin=task_origin,
            statement=(
                f"The local task profiles explicitly consume the official "
                f"SIESTA FDF label {label}."
            ),
            paths={entry["source_file"] for entry in matches},
            strength="required",
        )

    observable_to_marker = {
        "total_energy": "siesta: Final energy (eV)",
        "max_force": "siesta: Atomic forces (eV/Ang)",
    }
    output_observables = sorted(
        {
            observable
            for profile in tasks["profiles"].values()
            for observable in profile.get("required_output_observables", [])
        }
    )
    records_by_label = {
        record["label"]: record
        for record in supplements["records"]
        if record["kind"] == "output-marker"
    }
    for observable in output_observables:
        marker_label = observable_to_marker.get(observable)
        record = records_by_label.get(marker_label or "")
        if record is None:
            raise ValueError(
                f"no exact output-marker source for profile observable {observable}"
            )
        sid = semantic_id("siesta.profile-output", observable)
        add_release_subject(
            subject_id=sid,
            title=f"SIESTA task-profile output observable: {observable}",
            category="output-observable",
            subject_kind="observable",
            origin=task_origin,
            statement=(
                f"The task profile requires {observable}, tied to the exact "
                f"released-source output marker {marker_label}."
            ),
            paths=(record["source_file"],),
            strength="required",
        )

    portal_subjects: dict[str, dict[str, str]] = {}
    portal_attachments: dict[str, set[str]] = defaultdict(set)

    def add_portal_subject(
        *,
        subject_id: str,
        title: str,
        category: str,
        subject_kind: str,
        origin: dict[str, str],
        statement: str,
        locator: str,
        strength: str = "supporting",
    ) -> None:
        portal_subjects[subject_id] = provider_subject(
            subject_id, title, category, strength
        )
        scope_subjects[subject_id] = scope_subject(
            subject_id=subject_id,
            subject_kind=subject_kind,
            evidence_class="official-provider-required",
            origins=(origin,),
            statement=statement,
            provider_input_ids=("siesta-portal",),
        )
        portal_attachments[locator].add(subject_id)

    for source in registry["sources"]:
        sid = f"siesta.portal-topic.{safe_fragment(source['key'])}"
        locator = (
            PORTAL_PERFORMANCE_URL
            if source["key"] == "performance"
            else PORTAL_REFERENCE_URL
        )
        add_portal_subject(
            subject_id=sid,
            title=f"SIESTA 5.4 portal topic: {source['key']}",
            category="provenance",
            subject_kind="documented-claim",
            origin=registry_origin,
            statement=(
                f"The routing registry maps {source['key']} to the exact "
                "SIESTA 5.4 documentation line."
            ),
            locator=locator,
            strength="required",
        )

    for task_name in sorted(tasks["profiles"]):
        sid = f"siesta.task.{task_name}"
        add_portal_subject(
            subject_id=sid,
            title=f"SIESTA task profile: {task_name}",
            category="workflow",
            subject_kind="task",
            origin=task_origin,
            statement=(
                f"The {task_name} task profile requires surrounding official "
                "SIESTA 5.4 workflow documentation in addition to exact FDF "
                "label records."
            ),
            locator=PORTAL_REFERENCE_URL,
            strength="required",
        )

    for sid, title, locator in (
        (
            "siesta.portal.reference-manual",
            "SIESTA 5.4 consolidated reference manual",
            PORTAL_REFERENCE_URL,
        ),
        (
            "siesta.portal.performance-options",
            "SIESTA 5.4 performance options",
            PORTAL_PERFORMANCE_URL,
        ),
    ):
        add_portal_subject(
            subject_id=sid,
            title=title,
            category="provenance",
            subject_kind="documented-claim",
            origin=script_origin,
            statement=(
                f"The exact external bytes for {title} are recorded without "
                "embedding the documentation body."
            ),
            locator=locator,
        )

    scientific_checks = set(
        tasks["common"].get("required_scientific_checks", [])
    )
    parent_roles: set[str] = set()
    maturity_values: set[str] = set()
    for profile in tasks["profiles"].values():
        scientific_checks.update(profile.get("required_scientific_checks", []))
        parent_roles.update(profile.get("required_parent_roles", []))
        for key in (
            "input_maturity",
            "run_maturity",
            "task_validity_maturity",
        ):
            maturity_values.add(profile[key])

    for check in sorted(scientific_checks):
        sid = semantic_id("siesta.scientific-check", check)
        scope_subjects[sid] = scope_subject(
            subject_id=sid,
            subject_kind="claim",
            evidence_class="scientific-methodology",
            origins=(task_origin,),
            statement=(
                f"Scientific acceptance requires the case-specific check "
                f"{check}; official documentation alone cannot satisfy it."
            ),
        )
    for role in sorted(parent_roles):
        sid = semantic_id("siesta.parent-role", role)
        scope_subjects[sid] = scope_subject(
            subject_id=sid,
            subject_kind="workflow",
            evidence_class="deterministic-tool-behavior",
            origins=(task_origin,),
            statement=(
                f"The local lineage gate deterministically requests parent "
                f"artifact role {role}."
            ),
        )
    for maturity in sorted(maturity_values):
        sid = semantic_id("siesta.maturity", maturity)
        scope_subjects[sid] = scope_subject(
            subject_id=sid,
            subject_kind="limitation",
            evidence_class="repository-policy",
            origins=(task_origin,),
            statement=(
                f"The repository-local maturity label {maturity} limits "
                "automation claims and is not an upstream SIESTA statement."
            ),
        )

    source_hashes: dict[str, str] = {
        item["path"]: item["sha256"] for item in index["source_files"]
    }
    source_urls: dict[str, str] = {
        item["path"]: item["raw_url"] for item in index["source_files"]
    }
    for record in supplements["records"]:
        path = record["source_file"]
        source_hashes[path] = record["source_sha256"]
        source_urls[path] = RELEASE_ROOT + path
    if set(source_hashes) != release_paths or set(source_urls) != release_paths:
        raise ValueError("SIESTA exact-release source metadata is incomplete")

    release_sources = [
        external_source(
            identity=release_source_id(path),
            title=f"SIESTA 5.4.2 exact raw source: {path}",
            source_kind=(
                "source-documentation"
                if path.startswith("Docs/")
                else "source-documentation"
            ),
            locator=source_urls[path],
            raw_sha256=source_hashes[path],
            raw_bytes=RELEASE_SOURCE_BYTES[path],
            evidence_sha256=(
                sha256_file(index_path)
                if path.startswith("Docs/")
                else sha256_file(supplement_path)
            ),
            subject_ids=release_attachments[path],
        )
        for path in sorted(release_paths)
    ]
    if any(
        "/-/blob/" in source["locator"] or "#" in source["locator"]
        for source in release_sources
    ):
        raise ValueError("SIESTA canonical release locators must be raw/no-fragment")

    release_aggregate = sha256_text(
        "".join(source_hashes[path] for path in sorted(source_hashes))
    )
    release_catalog = {
        "schema_version": "1.0",
        "contract_name": "official-document-source-catalog",
        "version_scope": {
            "kind": "exact",
            "value": "5.4.2",
            "retrieved_utc": RETRIEVED_UTC,
            "snapshot_identity": {
                "kind": "revision",
                "value": RELEASE_COMMIT,
                "content_sha256": release_aggregate,
            },
        },
        "upstream_universe_complete": False,
        "inventory_locator": source_urls[sorted(source_urls)[0]],
        "sources": release_sources,
        "subjects": [
            release_subjects[key] for key in sorted(release_subjects)
        ],
        "reviewed_exclusions": [],
        "losses": [],
        "license": {
            "identity": {
                "identifier": "GPL-3.0-only",
                "terms_urls": [RELEASE_LICENSE_URL],
                "verification": "verified",
            },
            "assessment": "allowed",
            "allowed_storage_modes": [
                "metadata-only",
                "external-runtime-only",
            ],
            "official_terms_locator": RELEASE_LICENSE_URL,
            "limitations": [
                "The repository policy forbids embedded bundle content even "
                "though the exact release source license is known-open."
            ],
        },
        "limitations": [
            "The corpus is bounded to 47 manual TeX files and 6 released "
            "source files supporting FDF/output records; it is not the full "
            "SIESTA Docs or source tree.",
            "All raw bytes remain external; only hash, byte-count, locator, "
            "and semantic mapping metadata are retained.",
            "External whole-source selection receipts lack platform "
            "attestation, so coverage remains partial.",
        ],
        "blockers": [],
    }

    portal_sources = []
    for url, title in (
        (PORTAL_REFERENCE_URL, "SIESTA 5.4 consolidated reference manual"),
        (PORTAL_PERFORMANCE_URL, "SIESTA 5.4 performance options"),
    ):
        receipt = PORTAL_OBJECTS[url]
        portal_sources.append(
            external_source(
                identity=portal_source_id(url),
                title=title,
                source_kind="reference-page",
                locator=url,
                raw_sha256=receipt["sha256"],
                raw_bytes=receipt["bytes"],
                evidence_sha256=PORTAL_OBJECTS[PORTAL_LICENSE_URL]["sha256"],
                subject_ids=portal_attachments[url],
            )
        )
    portal_aggregate = sha256_text(
        "".join(
            PORTAL_OBJECTS[url]["sha256"]
            for url in (PORTAL_REFERENCE_URL, PORTAL_PERFORMANCE_URL)
        )
    )
    portal_catalog = {
        "schema_version": "1.0",
        "contract_name": "official-document-source-catalog",
        "version_scope": {
            "kind": "exact",
            "value": "5.4",
            "retrieved_utc": RETRIEVED_UTC,
            "snapshot_identity": {
                "kind": "manifest",
                "value": "siesta-5.4-two-page-external-receipt",
                "content_sha256": portal_aggregate,
            },
        },
        "upstream_universe_complete": False,
        "inventory_locator": PORTAL_REFERENCE_URL,
        "sources": sorted(portal_sources, key=lambda item: item["source_id"]),
        "subjects": [
            portal_subjects[key] for key in sorted(portal_subjects)
        ],
        "reviewed_exclusions": [],
        "losses": [],
        "license": {
            "identity": {
                "identifier": "CC-BY-NC-SA-4.0",
                "terms_urls": [PORTAL_LICENSE_URL],
                "verification": "verified",
            },
            "assessment": "conditional",
            "allowed_storage_modes": [
                "metadata-only",
                "external-runtime-only",
                "excluded",
            ],
            "official_terms_locator": PORTAL_LICENSE_URL,
            "limitations": [
                "The non-commercial share-alike documentation license and "
                "central authority policy prohibit embedding portal bodies."
            ],
        },
        "limitations": [
            "Only the consolidated 5.4 reference page and performance page "
            "have exact external receipts; the complete portal toctree is not "
            "inventoried.",
            "Portal documentation authority and 5.4.2 release-source "
            "authority remain separate corpora and license reviews.",
        ],
        "blockers": [],
    }

    generated_catalog_origins = {
        "siesta-portal": {
            "path": OUTPUTS["portal"].relative_to(REPO_ROOT).as_posix(),
            "sha256": sha256_bytes(canonical_json_bytes(portal_catalog)),
        },
        "siesta-release": {
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
        "extractor_id": "siesta-fdf-profile-semantic-v1",
        "subjects": [
            scope_subjects[key] for key in sorted(scope_subjects)
        ],
    }
    return {
        "portal": portal_catalog,
        "release": release_catalog,
        "scope": scope_catalog,
    }


TECHNICAL_AUTHORITY_PROJECTIONS: dict[str, dict[str, Any]] = {
    "portal": {
        "provider": {
            "provider_id": "siesta",
            "input_id": "siesta-portal",
        },
        "authority": {"authority_id": "siesta-official-docs"},
        "projection": {
            "canonical_urls": [
                "https://docs.siesta-project.org/projects/siesta/en/5.4/"
            ],
            "version_scopes": [
                {"scope": "exact", "exact_version": "5.4"}
            ],
        },
    },
    "release": {
        "provider": {
            "provider_id": "siesta",
            "input_id": "siesta-release",
        },
        "authority": {"authority_id": "siesta-release-source-docs"},
        "projection": {
            "canonical_urls": [RELEASE_ROOT],
            "version_scopes": [
                {"scope": "exact", "exact_version": "5.4.2"}
            ],
        },
    },
}


def _migrate_catalog(
    name: str,
    legacy_catalog: dict[str, Any],
    scope_catalog: dict[str, Any],
) -> dict[str, Any]:
    """Project one frozen v1.0 technical inventory through the central converter."""

    configuration = TECHNICAL_AUTHORITY_PROJECTIONS[name]
    legacy_bytes = canonical_json_bytes(legacy_catalog)
    included = [
        source
        for source in legacy_catalog["sources"]
        if source["disposition"] == "included"
    ]
    if not included:
        raise ValueError(f"{name}: no included source for inventory projection")
    return convert_catalog_v10_to_v11(
        legacy_catalog,
        provider=configuration["provider"],
        authority=configuration["authority"],
        authority_projection=configuration["projection"],
        scope_catalog=scope_catalog,
        inventory_projection={
            "locator": included[0]["locator"],
            "identity": {
                "sha256": sha256_bytes(legacy_bytes),
                "bytes": len(legacy_bytes),
            },
            "canonical_preimage_bytes": legacy_bytes,
        },
    )


def _bind_scope_to_v11_catalogs(
    scope_catalog: dict[str, Any],
    catalogs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Replace migration-preimage refs with exact checked-in v1.1 identities."""

    projected = copy.deepcopy(scope_catalog)
    identities = {
        OUTPUTS[name].relative_to(REPO_ROOT).as_posix(): sha256_bytes(
            output_json_bytes(name, catalogs[name])
        )
        for name in ("portal", "release")
    }
    for subject in projected["subjects"]:
        for origin in subject["origin_refs"]:
            if origin["path"] in identities:
                origin["sha256"] = identities[origin["path"]]
    return projected


def build_catalogs() -> dict[str, dict[str, Any]]:
    """Return final v1.1 catalogs without exposing legacy policy records."""

    legacy = _build_legacy_catalogs()
    migrated = {
        name: _migrate_catalog(name, legacy[name], legacy["scope"])
        for name in ("portal", "release")
    }
    migrated["scope"] = _bind_scope_to_v11_catalogs(
        legacy["scope"],
        migrated,
    )
    return migrated


def validate_catalogs(catalogs: dict[str, dict[str, Any]]) -> None:
    source_schema = load_json(
        REPO_ROOT
        / "contracts"
        / "official-document-source-catalog-1.1.schema.json"
    )
    scope_schema = load_json(
        REPO_ROOT
        / "contracts"
        / "official-document-scope-catalog.schema.json"
    )
    for name, data in catalogs.items():
        schema = scope_schema if name == "scope" else source_schema
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
            "sha256": sha256_bytes(output_json_bytes(name, catalogs[name])),
        }

    def migration_preimage_ref(name: str) -> dict[str, str]:
        return {
            "path": OUTPUTS[name].relative_to(REPO_ROOT).as_posix(),
            "sha256": catalogs[name]["inventory_identity"]["sha256"],
        }

    providers = [
        {
            "input_id": "siesta-portal",
            "adapter_id": "declarative-catalog-v1",
            "authority_id": "siesta-official-docs",
            "provider_id": "siesta",
            "source_ref": generated_ref("portal"),
        },
        {
            "input_id": "siesta-release",
            "adapter_id": "declarative-catalog-v1",
            "authority_id": "siesta-release-source-docs",
            "provider_id": "siesta",
            "source_ref": generated_ref("release"),
        },
    ]
    seed = {
        "schema_version": "1.0",
        "contract_name": "official-document-pack-seed",
        "skill_id": SKILL_ID,
        "status_ceiling": "partial",
        "scope_extractor_id": "siesta-fdf-profile-semantic-v1",
        "scope_catalog_ref": generated_ref("scope"),
        "providers": providers,
        "limitations": [
            "The portal catalog contains exact receipts for only two pages and "
            "does not enumerate the complete SIESTA 5.4 documentation toctree.",
            "The exact-release catalog is bounded to 47 manual TeX files and "
            "6 source supplements rather than the full release tree.",
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
                # Preserve the established local proposal identity: it records
                # the frozen v1.0 migration preimage, whereas the seed binds
                # the exact checked-in v1.1 catalog bytes.
                "source_catalog_ref": migration_preimage_ref(
                    "portal"
                    if provider["input_id"] == "siesta-portal"
                    else "release"
                ),
                "consumer_binding": {
                    "binding_id": (
                        "siesta-skill-siesta-docs"
                        if provider["input_id"] == "siesta-portal"
                        else "siesta-skill-siesta-release-source"
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
    for name in ("portal", "release"):
        for source in catalogs[name]["discovered_sources"].values():
            if source["disposition"] != "included":
                continue
            content = source["content"]
            if content["content_mode"] != "external-content":
                raise ValueError(
                    f"{name}: included source is not external-content"
                )
            receipt = content["receipt"]
            identity = (
                receipt["raw_sha256"],
                receipt["raw_bytes"],
            )
            locator = content["locator"]
            previous = expected.get(locator)
            if previous is not None and previous != identity:
                raise ValueError(
                    f"{name}: conflicting receipts for {locator}"
                )
            expected[locator] = identity
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
        payload = output_json_bytes(name, outputs[name])
        current = output.read_bytes() if output.is_file() else None
        if current == payload:
            continue
        stale.append(output.relative_to(REPO_ROOT).as_posix())
        if not check:
            atomic_write(output, payload)
    if check and stale:
        print(
            "ERROR: stale SIESTA source-pack catalogs: " + ", ".join(stale),
            file=sys.stderr,
        )
        return 2
    verb = "checked" if check else "synchronized"
    print(
        f"PASS: {verb} SIESTA metadata-only source-pack catalogs "
        f"(47+6 exact-release sources; 2 portal pages)"
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
