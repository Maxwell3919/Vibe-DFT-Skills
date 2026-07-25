#!/usr/bin/env python3
"""Generate exact-scope, metadata-only official-document pack inputs."""

from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable


SKILL_ID = "dft-postprocess"
EXTRACTOR_ID = "dft-postprocess-scope-v1"
RETRIEVED_UTC = "2026-07-24T00:00:00Z"
CP2K_MANIFEST_RELATIVE = (
    "skills/cp2k-rigorous-calculations/references/official-manual/manifest.json"
)
CP2K_RECEIPT_UTC = "2026-07-18T00:00:00Z"
CP2K_POSTPROCESS_TOPICS = {
    "band-structure": "Band-structure output",
    "density-cube": "Electron-density cube output",
    "dos": "DOS output",
}


def repository_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if parent.joinpath("registry", "skill-registry.yaml").is_file():
            return parent
    raise RuntimeError("cannot locate repository root")


ROOT = repository_root()
TOOLS = str(ROOT / "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

from registry_yaml import load_yaml_strict  # noqa: E402
from migrate_official_document_catalogs_v11 import (  # noqa: E402
    convert_catalog_v10_to_v11,
)
from official_source_authorities import validate_and_project  # noqa: E402


PROVIDER_SPECS = {
    "qe-7-5-postprocess": ("qe-official-docs", "qe"),
    "vasp-wiki-postprocess": ("vasp-official-wiki", "vasp"),
    "cp2k-2026-2-postprocess": ("cp2k-official-manual", "cp2k"),
    "siesta-5-4-2-postprocess": ("siesta-release-source-docs", "siesta"),
    "ase-3-29-postprocess": ("ase-release-source-docs-3-29-0", "ase"),
    "vaspkit-docs": ("vaspkit-1-5-documentation", "vaspkit"),
    "vesta-manual": ("vesta-official-manual", "vesta"),
    "bader-1-05": ("bader-1-05-official-page", "bader"),
}


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
        raise ValueError(f"cannot derive a safe id from {value!r}")
    return normalized


def origin(root: Path, relative: str) -> dict[str, str]:
    return {"path": relative, "sha256": sha256_file(root / relative)}


def observable_registry(root: Path) -> dict[str, Any]:
    path = root / "skills" / SKILL_ID / "references" / "observable-registry.yaml"
    value = load_yaml_strict(path, "observable-registry.yaml")
    if not isinstance(value, dict):
        raise ValueError("observable registry root must be a mapping")
    return value


def literal_subcommands(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    result: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_parser"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            result.add(node.args[0].value)
    return tuple(sorted(result))


def literal_assignment(path: Path, name: str) -> object:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f"{path}: missing literal assignment {name}")


def capability_inventory(root: Path) -> tuple[dict[str, str], tuple[str, ...]]:
    path = root / "skills" / SKILL_ID / "scripts" / "dftpost" / "capabilities.py"
    external = literal_assignment(path, "EXTERNAL_TOOLS")
    packages = literal_assignment(path, "PYTHON_PACKAGES")
    if not isinstance(external, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in external.items()
    ):
        raise ValueError("EXTERNAL_TOOLS is not a string mapping")
    if not isinstance(packages, tuple) or not all(
        isinstance(item, str) for item in packages
    ):
        raise ValueError("PYTHON_PACKAGES is not a string tuple")
    result = dict(external)
    result["visualization.vesta"] = "VESTA"
    return dict(sorted(result.items())), tuple(sorted(packages))


def registry_subjects(root: Path) -> list[dict[str, Any]]:
    registry = observable_registry(root)
    relative = f"skills/{SKILL_ID}/references/observable-registry.yaml"
    source_ref = origin(root, relative)
    subjects: list[dict[str, Any]] = []
    observables = registry.get("observables")
    backends = registry.get("backends")
    if not isinstance(observables, dict) or not isinstance(backends, dict):
        raise ValueError("observable registry lacks observables or backends")
    for observable_id, record in sorted(observables.items()):
        subjects.append(
            {
                "subject_id": f"observable:{observable_id}",
                "subject_kind": "observable",
                "evidence_class": "repository-policy",
                "origin_refs": [source_ref],
                "statement": (
                    f"The canonical registry declares the {observable_id!r} "
                    f"observable with dataset kind {record.get('dataset_kind')!r}."
                ),
                "expected_disposition": "not-applicable",
                "provider_input_ids": [],
            }
        )
    for backend_id, record in sorted(backends.items()):
        implemented = bool(record.get("implemented", False))
        subjects.append(
            {
                "subject_id": f"backend:{backend_id}",
                "subject_kind": "backend",
                "evidence_class": "repository-policy",
                "origin_refs": [source_ref],
                "statement": (
                    f"The canonical registry declares backend {backend_id!r}; "
                    f"implemented={implemented!s} and kind={record.get('kind')!r}."
                ),
                "expected_disposition": (
                    "not-applicable" if implemented else "excluded"
                ),
                "provider_input_ids": [],
            }
        )
    for observable_id, observable in sorted(observables.items()):
        codes = observable.get("codes")
        if not isinstance(codes, dict):
            raise ValueError(f"{observable_id}: codes must be a mapping")
        for code, route_group in sorted(codes.items()):
            routes = route_group.get("backend_routes")
            if not isinstance(routes, dict):
                raise ValueError(f"{observable_id}/{code}: backend_routes missing")
            for backend_id, route in sorted(routes.items()):
                maturity = route.get("maturity")
                subjects.append(
                    {
                        "subject_id": (
                            f"route:{observable_id}:{code}:{safe_id(backend_id)}"
                        ),
                        "subject_kind": "workflow",
                        "evidence_class": "repository-policy",
                        "origin_refs": [source_ref],
                        "statement": (
                            f"The registry route {observable_id}/{code}/{backend_id} "
                            f"has maturity {maturity!r}."
                        ),
                        "expected_disposition": (
                            "excluded"
                            if maturity == "design-only"
                            else "not-applicable"
                        ),
                        "provider_input_ids": [],
                    }
                )
    return subjects


def cli_subjects(root: Path) -> list[dict[str, Any]]:
    relative = f"skills/{SKILL_ID}/scripts/dftpost/cli.py"
    source_ref = origin(root, relative)
    return [
        {
            "subject_id": f"cli:{command}",
            "subject_kind": "task",
            "evidence_class": "deterministic-tool-behavior",
            "origin_refs": [source_ref],
            "statement": f"The dftpost CLI exposes the {command!r} subcommand.",
            "expected_disposition": "not-applicable",
            "provider_input_ids": [],
        }
        for command in literal_subcommands(root / relative)
    ]


SUPPORTED_EXTERNAL_PREFIXES = {
    "qe.": "qe-7-5-postprocess",
    "vasp.vaspkit": "vaspkit-docs",
    "charge.bader": "bader-1-05",
    "visualization.vesta": "vesta-manual",
}
SUPPORTED_PACKAGES = {"ase": "ase-3-29-postprocess"}


def capability_subjects(root: Path) -> list[dict[str, Any]]:
    relative = f"skills/{SKILL_ID}/scripts/dftpost/capabilities.py"
    source_ref = origin(root, relative)
    external, packages = capability_inventory(root)
    subjects: list[dict[str, Any]] = []
    for role, command in sorted(external.items()):
        subjects.append(
            {
                "subject_id": f"capability:external:{safe_id(role)}",
                "subject_kind": "executable",
                "evidence_class": "deterministic-tool-behavior",
                "origin_refs": [source_ref],
                "statement": (
                    f"The local capability probe checks command {command!r} "
                    f"for role {role!r}; detection does not establish support."
                ),
                "expected_disposition": "not-applicable",
                "provider_input_ids": [],
            }
        )
        covered = any(
            role == prefix or role.startswith(prefix)
            for prefix in SUPPORTED_EXTERNAL_PREFIXES
        )
        if not covered:
            subjects.append(
                {
                    "subject_id": f"provider-gap:external:{safe_id(role)}",
                    "subject_kind": "limitation",
                    "evidence_class": "repository-policy",
                    "origin_refs": [source_ref],
                    "statement": (
                        f"No exact official-document provider input is bound for "
                        f"the capability-only role {role!r}."
                    ),
                    "expected_disposition": "excluded",
                    "provider_input_ids": [],
                }
            )
    for package in packages:
        subjects.append(
            {
                "subject_id": f"capability:python:{safe_id(package)}",
                "subject_kind": "capability",
                "evidence_class": "deterministic-tool-behavior",
                "origin_refs": [source_ref],
                "statement": (
                    f"The local capability probe reports the installed version "
                    f"of Python package {package!r}; detection is not support."
                ),
                "expected_disposition": "not-applicable",
                "provider_input_ids": [],
            }
        )
        if package not in SUPPORTED_PACKAGES:
            subjects.append(
                {
                    "subject_id": f"provider-gap:python:{safe_id(package)}",
                    "subject_kind": "limitation",
                    "evidence_class": "repository-policy",
                    "origin_refs": [source_ref],
                    "statement": (
                        f"No exact official-document provider input is bound for "
                        f"the capability-only Python package {package!r}."
                    ),
                    "expected_disposition": "excluded",
                    "provider_input_ids": [],
                }
            )
    return subjects


def heading_subjects(root: Path) -> list[dict[str, Any]]:
    relative_paths = [
        f"skills/{SKILL_ID}/SKILL.md",
        f"skills/{SKILL_ID}/references/artifact-contracts.md",
        f"skills/{SKILL_ID}/references/observable-matrix.md",
        f"skills/{SKILL_ID}/references/plotting-and-evidence-standard.md",
        f"skills/{SKILL_ID}/references/tool-registry.md",
        f"skills/{SKILL_ID}/references/validation-data-policy.md",
    ]
    subjects: list[dict[str, Any]] = []
    for relative in relative_paths:
        path = root / relative
        source_ref = origin(root, relative)
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^(#{1,3})\s+(.+?)\s*$", line)
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
                            for token in ("limit", "unsupported", "fail", "do not")
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


PROVIDER_SUBJECTS: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "qe:bands-artifacts",
        "output-field",
        "QE bands artifacts and their producer interface are provider-defined.",
        "qe-7-5-postprocess",
        "partial",
    ),
    (
        "qe:dos-projection-artifacts",
        "output-field",
        "QE DOS and projected-DOS artifacts are provider-defined.",
        "qe-7-5-postprocess",
        "partial",
    ),
    (
        "qe:phonon-epc-artifacts",
        "output-field",
        "QE phonon and EPC postprocessing artifacts are provider-defined.",
        "qe-7-5-postprocess",
        "partial",
    ),
    (
        "qe:grid-artifacts",
        "output-field",
        "QE pp.x real-space outputs are provider-defined.",
        "qe-7-5-postprocess",
        "partial",
    ),
    (
        "vasp:output-artifacts",
        "output-field",
        "VASP output artifact formats consumed by local parsers are provider-defined.",
        "vasp-wiki-postprocess",
        "partial",
    ),
    (
        "cp2k:postprocess-artifacts",
        "output-field",
        "CP2K bands, DOS, and real-space artifact controls are provider-defined.",
        "cp2k-2026-2-postprocess",
        "partial",
    ),
    (
        "siesta:postprocess-artifacts",
        "output-field",
        "SIESTA bands, DOS, and real-space output controls are provider-defined.",
        "siesta-5-4-2-postprocess",
        "partial",
    ),
    (
        "ase:structure-views",
        "capability",
        "ASE structure I/O and visualization semantics underpin structure views.",
        "ase-3-29-postprocess",
        "partial",
    ),
    (
        "vaspkit:band-table",
        "output-field",
        "VASPKIT band-table and k-label outputs are provider-defined.",
        "vaspkit-docs",
        "partial",
    ),
    (
        "vesta:command-line",
        "executable",
        "VESTA command-line behavior is provider-defined.",
        "vesta-manual",
        "partial",
    ),
    (
        "bader:acf-format",
        "output-field",
        "The ACF.dat field convention is defined by the Bader provider.",
        "bader-1-05",
        "partial",
    ),
)


def provider_scope_subjects(root: Path) -> list[dict[str, Any]]:
    origin_by_input = {
        "qe-7-5-postprocess": f"skills/{SKILL_ID}/scripts/dftpost/phonon_epc.py",
        "vasp-wiki-postprocess": f"skills/{SKILL_ID}/scripts/dftpost/vasp_electronic.py",
        "cp2k-2026-2-postprocess": f"skills/{SKILL_ID}/references/tool-registry.md",
        "siesta-5-4-2-postprocess": f"skills/{SKILL_ID}/references/observable-registry.yaml",
        "ase-3-29-postprocess": f"skills/{SKILL_ID}/scripts/dftpost/structure_views.py",
        "vaspkit-docs": f"skills/{SKILL_ID}/scripts/dftpost/vaspkit.py",
        "vesta-manual": f"skills/{SKILL_ID}/scripts/dftpost/vesta.py",
        "bader-1-05": f"skills/{SKILL_ID}/scripts/dftpost/realspace.py",
    }
    return [
        {
            "subject_id": subject_id,
            "subject_kind": subject_kind,
            "evidence_class": "official-provider-required",
            "origin_refs": [origin(root, origin_by_input[input_id])],
            "statement": statement,
            "expected_disposition": disposition,
            "provider_input_ids": [input_id],
        }
        for subject_id, subject_kind, statement, input_id, disposition in PROVIDER_SUBJECTS
    ]


def scope_catalog(root: Path) -> dict[str, Any]:
    subjects = (
        registry_subjects(root)
        + cli_subjects(root)
        + capability_subjects(root)
        + heading_subjects(root)
        + provider_scope_subjects(root)
    )
    subjects.sort(key=lambda item: item["subject_id"])
    ids = [item["subject_id"] for item in subjects]
    if len(ids) != len(set(ids)):
        duplicates = sorted(
            item for item, count in Counter(ids).items() if count > 1
        )
        raise ValueError(f"scope extractor produced duplicate ids: {duplicates}")
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
    identity_kind: str,
    identity_value: str,
    sha256: str,
    size: int,
    subject_ids: Iterable[str],
    retrieved_utc: str = RETRIEVED_UTC,
    retrieval_method: str = "https-get",
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "title": title,
        "source_kind": source_kind,
        "locator": locator,
        "disposition": "included",
        "external_identity": {
            "kind": identity_kind,
            "value": identity_value,
            "raw_sha256": sha256,
            "raw_bytes": size,
            "retrieved_utc": retrieved_utc,
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
                    "retrieval_method": retrieval_method,
                    "retrieved_utc": retrieved_utc,
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


def provider_subject_records(input_id: str) -> list[dict[str, str]]:
    return [
        {
            "subject_id": subject_id,
            "title": statement,
            "category": (
                "output-observable"
                if subject_kind == "output-field"
                else "workflow"
            ),
            "requirement_strength": "required",
            "evidence_class": "official-provider-required",
        }
        for subject_id, subject_kind, statement, selected_input, _ in PROVIDER_SUBJECTS
        if selected_input == input_id
    ]


def catalog(
    *,
    input_id: str,
    version_scope: dict[str, Any],
    inventory_locator: str,
    sources: list[dict[str, Any]],
    license_identifier: str | None,
    terms_url: str,
    license_assessment: str,
    limitations: list[str],
    reviewed_exclusions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "contract_name": "official-document-source-catalog",
        "version_scope": version_scope,
        "upstream_universe_complete": False,
        "inventory_locator": inventory_locator,
        "sources": sources,
        "subjects": provider_subject_records(input_id),
        "reviewed_exclusions": (
            reviewed_exclusions if reviewed_exclusions is not None else []
        ),
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
                "Only metadata and external receipts are stored; provider text is not embedded."
            ],
        },
        "limitations": limitations,
        "blockers": [],
    }


def exact_scope(value: str) -> dict[str, Any]:
    return {
        "kind": "exact",
        "value": value,
        "retrieved_utc": None,
        "snapshot_identity": None,
    }


def revision_scope(value: str) -> dict[str, Any]:
    return {
        "kind": "revision",
        "value": value,
        "retrieved_utc": None,
        "snapshot_identity": None,
    }


def cp2k_canonical_source_id(source_path: str) -> str:
    source_id = source_path.lower().replace("/", ".")
    if safe_id(source_id) != source_id:
        raise ValueError(
            f"CP2K canonical source path does not map to a safe id: {source_path!r}"
        )
    return source_id


def cp2k_curated_partition(
    root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    manifest_path = root / CP2K_MANIFEST_RELATIVE
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pages = manifest.get("pages")
    if (
        manifest.get("manual_version") != "2026.2"
        or not isinstance(pages, dict)
        or manifest.get("mirrored_topic_count") != len(pages)
    ):
        raise ValueError(
            f"{CP2K_MANIFEST_RELATIVE}: invalid CP2K 2026.2 curated manifest"
        )
    missing_topics = sorted(set(CP2K_POSTPROCESS_TOPICS) - set(pages))
    if missing_topics:
        raise ValueError(
            f"{CP2K_MANIFEST_RELATIVE}: missing selected topics {missing_topics}"
        )
    reviewed_utc = manifest.get("retrieved_utc")
    if not isinstance(reviewed_utc, str) or not reviewed_utc:
        raise ValueError(
            f"{CP2K_MANIFEST_RELATIVE}: missing manifest retrieval timestamp"
        )

    sources: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    source_ids: set[str] = set()
    for topic, page in sorted(pages.items()):
        if not isinstance(page, dict):
            raise ValueError(
                f"{CP2K_MANIFEST_RELATIVE}: invalid page record {topic!r}"
            )
        required = {
            "source_path": str,
            "source_url": str,
            "raw_sha256": str,
            "raw_bytes": int,
        }
        for key, expected_type in required.items():
            if not isinstance(page.get(key), expected_type):
                raise ValueError(
                    f"{CP2K_MANIFEST_RELATIVE}: {topic!r} lacks valid {key}"
                )
        source_id = cp2k_canonical_source_id(page["source_path"])
        if source_id in source_ids:
            raise ValueError(
                f"{CP2K_MANIFEST_RELATIVE}: duplicate canonical id {source_id!r}"
            )
        source_ids.add(source_id)
        if topic in CP2K_POSTPROCESS_TOPICS:
            title = f"CP2K 2026.2 {CP2K_POSTPROCESS_TOPICS[topic]}"
            sources.append(
                external_source(
                    source_id=source_id,
                    title=title,
                    source_kind="manual-page",
                    locator=page["source_url"],
                    identity_kind="revision",
                    identity_value="cp2k-2026.2",
                    sha256=page["raw_sha256"],
                    size=page["raw_bytes"],
                    subject_ids=["cp2k:postprocess-artifacts"],
                    retrieved_utc=CP2K_RECEIPT_UTC,
                )
            )
            continue
        exclusions.append(
            {
                "source_id": source_id,
                "title": (
                    "CP2K 2026.2 curated page: "
                    f"{page['source_path']}"
                ),
                "locator": page["source_url"],
                "reason_code": "out-of-scope",
                "rationale": (
                    "This page is present in the central curated CP2K 2026.2 "
                    "manifest but is outside the three postprocessing "
                    "artifact-control pages selected by this consumer catalog."
                ),
                "reviewed_utc": reviewed_utc,
            }
        )
    return sources, exclusions


def legacy_provider_catalogs(root: Path) -> dict[str, dict[str, Any]]:
    qe_sources = [
        (
            "qe-input-bands",
            "QE 7.5 INPUT_BANDS",
            "https://www.quantum-espresso.org/Doc/INPUT_BANDS.txt",
            "b8b1193c4f2723310151d7825240f9b20fe2212d1e0f509cce89988a93f7a14a",
            6604,
            ["qe:bands-artifacts"],
        ),
        (
            "qe-input-dos",
            "QE 7.5 INPUT_DOS",
            "https://www.quantum-espresso.org/Doc/INPUT_DOS.txt",
            "d18fa270d3ca41b3bed586c40bb9cf5fb2b67962e741381a75bea23b6601eff3",
            5896,
            ["qe:dos-projection-artifacts"],
        ),
        (
            "qe-input-projwfc",
            "QE 7.5 INPUT_PROJWFC",
            "https://www.quantum-espresso.org/Doc/INPUT_PROJWFC.txt",
            "2fe26603465c910cec30dd5da42fb157e6e9135b8d099e01130833232df8c01c",
            14081,
            ["qe:dos-projection-artifacts"],
        ),
        (
            "qe-input-pp",
            "QE 7.5 INPUT_PP",
            "https://www.quantum-espresso.org/Doc/INPUT_PP.html",
            "482dc70016a4638b18eca0219e56754e09fa195524a55decd6df3e6fbc5efd1c",
            57125,
            ["qe:grid-artifacts"],
        ),
        (
            "qe-input-q2r",
            "QE 7.5 INPUT_Q2R",
            "https://www.quantum-espresso.org/Doc/INPUT_Q2R.txt",
            "d493ae0332d60c865e904223a7db8a6b426570c1a07032946e186c869d5ca4ea",
            7356,
            ["qe:phonon-epc-artifacts"],
        ),
        (
            "qe-input-matdyn",
            "QE 7.5 INPUT_MATDYN",
            "https://www.quantum-espresso.org/Doc/INPUT_MATDYN.txt",
            "e162a380590814b4ce7bce383261cbcae2567f7e9c21de8655af446082691b91",
            20467,
            ["qe:phonon-epc-artifacts"],
        ),
        (
            "qe-input-dynmat",
            "QE 7.5 INPUT_DYNMAT",
            "https://www.quantum-espresso.org/Doc/INPUT_DYNMAT.txt",
            "4da654f7ed8ec6ceb5d38a4e470389b2fb414999eb5233e083ea454c2669470e",
            8143,
            ["qe:phonon-epc-artifacts"],
        ),
    ]
    vasp_pages = [
        ("CHGCAR", 4, 37118, "128d03063c9f8eddd05282fd8d1ca9ca3dfbd77c93ef2d6f6aec57464b26915f", 22456),
        ("DOSCAR", 429, 34299, "42827301bb98846e102dd10bb4b3a0a2c54c3e67d0d82a0597afda761007ee88", 14298),
        ("EIGENVAL", 427, 30963, "ff28c465fd905e964512a3e0f455d08f2ae2a274aa17a2ff9ffc238ba7afb9f5", 3211),
        ("KPOINTS", 1389, 35974, "2a27d4224470d21ef7f5a37d8fec5d95ba215da17e8c3be5efedb031a56f2c58", 93636),
        ("OUTCAR", 612, 36630, "6a1c480c3ce2f65ad785f445387e77b25193df892726b46e43574c3f7634a26a", 13403),
        ("POSCAR", 1387, 32299, "5ed1ff26e720087cc55444fcd02f697bf9e86b0d3bd4a6283e51b286b94e6c87", 54329),
        ("PROCAR", 430, 35404, "c220ff5032db1a32759b00c74de1ea4908b8963e4f6c396b28ca6c1ec50edc16", 12758),
        ("Vasprun.xml", 2181, 37162, "139da8b05e456731d6105660634b05337d1b520e19b4341849fa124f1e718923", 89760),
    ]
    cp2k_sources, cp2k_exclusions = cp2k_curated_partition(root)
    siesta_commit = "e486d12067b96ff688179f0496d0ec21b6fae0ab"
    siesta_sources = [
        ("siesta-band-structure", "SIESTA band-structure documentation", "Options/Band_structure_analysis.tex", "12cb1cddd52ce638e52176efe7bf26aaaa9ea07f753e699a4021e5d72fa9b9ef", 5141),
        ("siesta-density-of-states", "SIESTA density-of-states documentation", "Options/Density_of_states.tex", "387cc442a4a21a24cf7b709346dbc65f57f7929ccea82fc43cba3c43923bee81", 8033),
        ("siesta-grid-output", "SIESTA charge-density and potential output documentation", "Options/Output_charge_density_potential.tex", "a19bc0811789995e4bedba44aef961db6600ac9b79ee9ab04058b26234910673", 9403),
    ]
    ase_revision = "f27c0005ae6a67ea419f996e728668865bfc1f86"
    vaspkit_revision = "383a7103505b5b9436dedbf04df42ebb6e248638"
    return {
        "qe-7-5-postprocess": catalog(
            input_id="qe-7-5-postprocess",
            version_scope=exact_scope("7.5"),
            inventory_locator="https://www.quantum-espresso.org/Doc/",
            sources=[
                external_source(
                    source_id=source_id,
                    title=title,
                    source_kind="reference-page",
                    locator=url,
                    identity_kind="external-receipt",
                    identity_value=f"qe-7.5:{source_id}",
                    sha256=sha,
                    size=size,
                    subject_ids=subjects,
                    retrieved_utc="2026-07-17T11:49:00Z",
                )
                for source_id, title, url, sha, size, subjects in qe_sources
            ],
            license_identifier=None,
            terms_url="https://www.quantum-espresso.org/Doc/user_guide/node6.html",
            license_assessment="unresolved",
            limitations=[
                "The selected pages are version-labeled but the official web corpus remains rolling and incomplete."
            ],
        ),
        "vasp-wiki-postprocess": catalog(
            input_id="vasp-wiki-postprocess",
            version_scope={
                "kind": "latest-at-retrieval",
                "value": None,
                "retrieved_utc": "2026-07-17T12:42:00Z",
                "snapshot_identity": None,
            },
            inventory_locator="https://www.vasp.at/wiki/The_VASP_Manual",
            sources=[
                external_source(
                    source_id=f"vasp-{safe_id(title.lower())}",
                    title=f"VASP Wiki {title}",
                    source_kind="api-record",
                    locator=f"https://www.vasp.at/wiki/{title}",
                    identity_kind="revision",
                    identity_value=f"pageid:{pageid}:revid:{revid}",
                    sha256=sha,
                    size=size,
                    subject_ids=["vasp:output-artifacts"],
                    retrieved_utc="2026-07-17T12:42:00Z",
                    retrieval_method="official-api",
                )
                for title, pageid, revid, sha, size in vasp_pages
            ],
            license_identifier="GFDL-1.2-only",
            terms_url="https://www.vasp.at/wiki/Main_page",
            license_assessment="conditional",
            limitations=[
                "Wiki revisions do not establish VASP executable or POTCAR rights."
            ],
        ),
        "cp2k-2026-2-postprocess": catalog(
            input_id="cp2k-2026-2-postprocess",
            version_scope=exact_scope("2026.2"),
            inventory_locator="https://manual.cp2k.org/cp2k-2026_2-branch/",
            sources=cp2k_sources,
            license_identifier=None,
            terms_url="https://github.com/cp2k/cp2k/blob/v2026.2/LICENSE",
            license_assessment="unresolved",
            limitations=[
                "The manual documentation-license scope and CP2K external-tool repositories remain separate."
            ],
            reviewed_exclusions=cp2k_exclusions,
        ),
        "siesta-5-4-2-postprocess": catalog(
            input_id="siesta-5-4-2-postprocess",
            version_scope=exact_scope("5.4.2"),
            inventory_locator=(
                f"https://gitlab.com/siesta-project/siesta/-/tree/{siesta_commit}/Docs"
            ),
            sources=[
                external_source(
                    source_id=source_id,
                    title=title,
                    source_kind="source-documentation",
                    locator=(
                        "https://gitlab.com/siesta-project/siesta/-/raw/"
                        f"{siesta_commit}/Docs/tex/sections/{path}"
                    ),
                    identity_kind="revision",
                    identity_value=siesta_commit,
                    sha256=sha,
                    size=size,
                    subject_ids=["siesta:postprocess-artifacts"],
                )
                for source_id, title, path, sha, size in siesta_sources
            ],
            license_identifier="GPL-3.0-only",
            terms_url=(
                "https://gitlab.com/siesta-project/siesta/-/raw/"
                f"{siesta_commit}/COPYING"
            ),
            license_assessment="conditional",
            limitations=[
                "The selected release-source documentation is not the complete SIESTA postprocessing universe."
            ],
        ),
        "ase-3-29-postprocess": catalog(
            input_id="ase-3-29-postprocess",
            version_scope=exact_scope("3.29.0"),
            inventory_locator=f"https://gitlab.com/ase/ase/-/tree/{ase_revision}/doc",
            sources=[
                external_source(
                    source_id="ase-io-doc",
                    title="ASE 3.29.0 I/O documentation",
                    source_kind="source-documentation",
                    locator=(
                        f"https://gitlab.com/ase/ase/-/raw/{ase_revision}/"
                        "doc/ase/io/io.rst"
                    ),
                    identity_kind="revision",
                    identity_value=ase_revision,
                    sha256="f9ff991bae9525683fefafa704205de934a88c3399d9912ae64bc26e930f2078",
                    size=5187,
                    subject_ids=["ase:structure-views"],
                )
            ],
            license_identifier="LGPL-2.1-or-later",
            terms_url=f"https://gitlab.com/ase/ase/-/raw/{ase_revision}/LICENSE",
            license_assessment="conditional",
            limitations=[
                "Only the ASE surface directly consumed by structure views is selected."
            ],
        ),
        "vaspkit-docs": catalog(
            input_id="vaspkit-docs",
            version_scope=revision_scope(vaspkit_revision),
            inventory_locator=(
                f"https://github.com/vaspkit/vaspkit.github.io/tree/{vaspkit_revision}"
            ),
            sources=[
                external_source(
                    source_id="vaspkit-tutorials",
                    title="VASPKIT tutorial source",
                    source_kind="source-documentation",
                    locator=(
                        "https://raw.githubusercontent.com/vaspkit/vaspkit.github.io/"
                        f"{vaspkit_revision}/_sources/tutorials.rst.txt"
                    ),
                    identity_kind="revision",
                    identity_value=vaspkit_revision,
                    sha256="5a3f882c267b8da23d029861b9cbde3b9213f31e551b12df5e4bdc86e0bf6c59",
                    size=149377,
                    subject_ids=["vaspkit:band-table"],
                )
            ],
            license_identifier=None,
            terms_url="https://vaspkit.com/installation.html",
            license_assessment="unresolved",
            limitations=[
                "The documentation commit does not establish exact binary identity or redistribution rights."
            ],
        ),
        "vesta-manual": catalog(
            input_id="vesta-manual",
            version_scope={
                "kind": "latest-at-retrieval",
                "value": None,
                "retrieved_utc": RETRIEVED_UTC,
                "snapshot_identity": None,
            },
            inventory_locator="https://jp-minerals.org/vesta/en/doc/VESTA.html",
            sources=[
                external_source(
                    source_id="vesta-command-line",
                    title="VESTA command-line manual",
                    source_kind="manual-page",
                    locator="https://jp-minerals.org/vesta/en/doc/VESTAch17.html",
                    identity_kind="external-receipt",
                    identity_value="vesta-manual-retrieved-2026-07-24",
                    sha256="9ccdb26b2c7927b48f24d217d17d59b8b8043db09cb713ace96e8a863fca57df",
                    size=12093,
                    subject_ids=["vesta:command-line"],
                )
            ],
            license_identifier="LicenseRef-VESTA",
            terms_url="https://jp-minerals.org/vesta/en/download.html",
            license_assessment="conditional",
            limitations=[
                "The rolling manual is not bound to an exact installed VESTA executable."
            ],
        ),
        "bader-1-05": catalog(
            input_id="bader-1-05",
            version_scope=exact_scope("1.05"),
            inventory_locator="https://theory.cm.utexas.edu/henkelman/code/bader/",
            sources=[
                external_source(
                    source_id="bader-program-page",
                    title="Henkelman-group Bader program page",
                    source_kind="reference-page",
                    locator="https://theory.cm.utexas.edu/henkelman/code/bader/",
                    identity_kind="external-receipt",
                    identity_value="bader-1.05-page-retrieved-2026-07-24",
                    sha256="8e00e013e694a6cbf4cc17304b8c99139f37ecfdd7d6537e5066f3b93700960c",
                    size=15943,
                    subject_ids=["bader:acf-format"],
                )
            ],
            license_identifier="GPL-3.0-or-later",
            terms_url="https://theory.cm.utexas.edu/henkelman/code/",
            license_assessment="conditional",
            limitations=[
                "The page does not provide a Git tag; the source archive still needs an exact archive digest."
            ],
        ),
    }


def authority_projections(root: Path) -> dict[str, dict[str, Any]]:
    """Return the central technical authority projections used by v1.1."""

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
        raise ValueError(
            "invalid central technical authority projection: "
            + " | ".join(str(item) for item in failures)
        )
    return projections


def provider_catalogs(root: Path) -> dict[str, dict[str, Any]]:
    """Generate v1.1 catalogs by pure conversion of deterministic v1.0 inputs."""

    legacy_catalogs = legacy_provider_catalogs(root)
    if set(legacy_catalogs) != set(PROVIDER_SPECS):
        raise ValueError(
            "provider specification mismatch: "
            f"catalogs={sorted(legacy_catalogs)} specs={sorted(PROVIDER_SPECS)}"
        )
    projections = authority_projections(root)
    scope = scope_catalog(root)
    catalogs: dict[str, dict[str, Any]] = {}
    for input_id, legacy in sorted(legacy_catalogs.items()):
        authority_id, provider_id = PROVIDER_SPECS[input_id]
        projection = projections.get(authority_id)
        if projection is None:
            raise ValueError(
                f"{input_id}: missing technical authority projection {authority_id}"
            )
        included = [
            source
            for source in legacy["sources"]
            if source.get("disposition") == "included"
        ]
        if not included:
            raise ValueError(f"{input_id}: no included legacy source")
        legacy_bytes = canonical_json_bytes(legacy)
        catalogs[input_id] = convert_catalog_v10_to_v11(
            legacy,
            provider={
                "input_id": input_id,
                "authority_id": authority_id,
                "provider_id": provider_id,
            },
            authority={"authority_id": authority_id},
            authority_projection=projection,
            scope_catalog=scope,
            inventory_projection={
                "locator": included[0]["locator"],
                "identity": {
                    "sha256": sha256_bytes(legacy_bytes),
                    "bytes": len(legacy_bytes),
                },
                "canonical_preimage_bytes": legacy_bytes,
            },
        )
    return catalogs


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
    provider_id: str,
    version_scope: dict[str, Any],
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
        "provider_class": "software",
        "provider_id": provider_id,
        "allowed_https_origins": origins,
        "version_policy": {
            "allowed_scopes": [version_scope["scope"]],
            "registered_scopes": [version_scope],
        },
        "content_policy": {
            "source_kinds": [
                "official-manual",
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


def exact_registry_scope(value: str) -> dict[str, Any]:
    return {
        "scope": "exact",
        "exact_version": value,
        "minimum_version": None,
        "maximum_version": None,
        "release_series": None,
    }


def latest_registry_scope() -> dict[str, Any]:
    return {
        "scope": "latest-at-retrieval",
        "exact_version": None,
        "minimum_version": None,
        "maximum_version": None,
        "release_series": None,
    }


def authority_proposal() -> dict[str, Any]:
    ase_revision = "f27c0005ae6a67ea419f996e728668865bfc1f86"
    vaspkit_revision = "383a7103505b5b9436dedbf04df42ebb6e248638"
    existing = (
        ("qe-official-docs", "qe", "qe-docs"),
        ("vasp-official-wiki", "vasp", "vasp-wiki"),
        ("cp2k-official-manual", "cp2k", "cp2k-manual"),
        (
            "siesta-release-source-docs",
            "siesta",
            "siesta-release-source",
        ),
    )
    return {
        "schema_version": "1.0",
        "proposal_type": "official-source-authority-and-consumer-bindings",
        "skill_id": SKILL_ID,
        "lifecycle_effect": "none",
        "authorities": [
            proposed_authority(
                authority_id="ase-release-source-docs-3-29-0",
                display_name="ASE 3.29.0 release-source documentation",
                provider_id="ase",
                version_scope=exact_registry_scope("3.29.0"),
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
                    "Only the ASE structure-I/O surface consumed by this pack "
                    "is selected."
                ),
            ),
            proposed_authority(
                authority_id="vaspkit-1-5-documentation",
                display_name="VASPKIT 1.5 documentation repository revision",
                provider_id="vaspkit",
                version_scope=exact_registry_scope(vaspkit_revision),
                origins=["https://raw.githubusercontent.com"],
                path_prefixes=[
                    f"/vaspkit/vaspkit.github.io/{vaspkit_revision}/"
                ],
                fact_urls=[
                    (
                        "https://raw.githubusercontent.com/vaspkit/"
                        f"vaspkit.github.io/{vaspkit_revision}/"
                        "_sources/tutorials.rst.txt"
                    )
                ],
                binding_suffix="vaspkit-docs",
                limitation=(
                    "The documentation revision does not establish exact "
                    "VASPKIT binary identity or redistribution rights."
                ),
            ),
            proposed_authority(
                authority_id="vesta-official-manual",
                display_name="VESTA official rolling manual",
                provider_id="vesta",
                version_scope=latest_registry_scope(),
                origins=["https://jp-minerals.org"],
                path_prefixes=["/vesta/en/doc/"],
                fact_urls=[
                    "https://jp-minerals.org/vesta/en/doc/VESTAch17.html"
                ],
                binding_suffix="vesta-manual",
                limitation=(
                    "The rolling manual is not bound to an exact installed "
                    "VESTA executable, and its license remains separately reviewed."
                ),
            ),
            proposed_authority(
                authority_id="bader-1-05-official-page",
                display_name="Henkelman-group Bader 1.05 official page",
                provider_id="bader",
                version_scope=exact_registry_scope("1.05"),
                origins=["https://theory.cm.utexas.edu"],
                path_prefixes=["/henkelman/code/bader/"],
                fact_urls=[
                    "https://theory.cm.utexas.edu/henkelman/code/bader/"
                ],
                binding_suffix="bader-page",
                limitation=(
                    "The rolling program page identifies version 1.05 but does "
                    "not provide a Git revision for the source archive."
                ),
            ),
        ],
        "existing_authority_bindings": [
            {
                "authority_id": authority_id,
                "provider_class": "software",
                "provider_id": provider_id,
                "consumer_binding": consumer_binding(
                    authority_id,
                    provider_id,
                    suffix=suffix,
                ),
            }
            for authority_id, provider_id, suffix in existing
        ],
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
                ("vesta", "visualization-tool"),
                ("bader", "postprocess-tool"),
            )
        ],
        "central_blockers": [
            "Add all eight consumer bindings before running the production pack builder.",
            "Reconcile the new VASPKIT exact-revision authority with the existing planned vaspkit-official-reference placeholder through an explicit reviewed registry change.",
            "Create or review the ASE, VESTA, and Bader software provider identities before activating their software-class authorities.",
            "Keep every new authority metadata-only until central license review resolves redistribution rights.",
        ],
        "invariants": [
            "No proposal changes Skill/software lifecycle, routing, installability, execution permission, or claim ceiling.",
            "Provider documentation does not promote design-only routes or establish native executable availability.",
        ],
    }


def build_outputs(root: Path) -> dict[Path, bytes]:
    skill_root = root / "skills" / SKILL_ID
    scope_path = skill_root / "references" / "source-pack-scope.json"
    outputs: dict[Path, bytes] = {
        scope_path: canonical_json_bytes(scope_catalog(root))
    }
    providers: list[dict[str, Any]] = []
    for input_id, value in sorted(provider_catalogs(root).items()):
        path = (
            skill_root / "references" / "source-pack-inputs" / f"{input_id}.json"
        )
        payload = canonical_json_bytes(value)
        outputs[path] = payload
        authority_id, provider_id = PROVIDER_SPECS[input_id]
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
        "status_ceiling": "blocked",
        "scope_extractor_id": "dft-postprocess-scope-v1",
        "scope_catalog_ref": {
            "path": scope_path.relative_to(root).as_posix(),
            "sha256": sha256_bytes(outputs[scope_path]),
        },
        "providers": providers,
        "limitations": [
            "The pack stores metadata and receipts only and does not embed provider text.",
            "Route maturity is copied exactly from the canonical observable registry and is never raised.",
        ],
        "blockers": [
            "Capability-only providers without exact authorities remain explicit excluded gaps.",
            "CP2K input/output tools, critic2, phonopy, pymatgen, py4vasp, Sumo, PyProcar, Wannier90, and several Python libraries lack exact provider bindings.",
        ],
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
