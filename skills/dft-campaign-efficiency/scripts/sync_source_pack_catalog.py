#!/usr/bin/env python3
"""Generate the deterministic official-document pack inputs for this Skill."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable


SKILL_ID = "dft-campaign-efficiency"
EXTRACTOR_ID = "dft-campaign-efficiency-scope-v1"
QE_COMMIT = "770a0b2d12928a67048e2f3da8d10d057e52179e"
RETRIEVED_UTC = "2026-07-24T00:00:00Z"


def _locate_repository_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if parent.joinpath("registry", "skill-registry.yaml").is_file():
            return parent
    raise RuntimeError("cannot locate repository root")


REPOSITORY_ROOT = _locate_repository_root()
CENTRAL_TOOLS = REPOSITORY_ROOT / "tools"
if str(CENTRAL_TOOLS) not in sys.path:
    sys.path.insert(0, str(CENTRAL_TOOLS))

from migrate_official_document_catalogs_v11 import (  # noqa: E402
    canonical_json_bytes,
    convert_catalog_v10_to_v11,
)
from official_source_authorities import validate_and_project  # noqa: E402
from registry_yaml import load_yaml_strict  # noqa: E402


def repository_root() -> Path:
    return REPOSITORY_ROOT


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def safe_id(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._:-]+", "-", value.strip()).strip("-")
    if not normalized:
        raise ValueError(f"cannot derive a subject id from {value!r}")
    return normalized


def origin(root: Path, relative: str) -> dict[str, str]:
    path = root / relative
    return {"path": relative, "sha256": sha256_file(path)}


def heading_subjects(root: Path) -> list[dict[str, Any]]:
    skill_root = root / "skills" / SKILL_ID
    relative_paths = [
        f"skills/{SKILL_ID}/SKILL.md",
        f"skills/{SKILL_ID}/references/case-first-learning.md",
        f"skills/{SKILL_ID}/references/comparability-and-evidence.md",
        f"skills/{SKILL_ID}/references/experience-lifecycle.md",
        f"skills/{SKILL_ID}/references/phonon-tc-efficiency.md",
        f"skills/{SKILL_ID}/references/record-schema-and-privacy.md",
    ]
    subjects: list[dict[str, Any]] = []
    for relative in relative_paths:
        path = root / relative
        source_ref = origin(root, relative)
        stem = path.stem
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^(#{1,4})\s+(.+?)\s*$", line)
            if match is None:
                continue
            title = match.group(2)
            if match.group(1) == "#" and path == skill_root / "SKILL.md":
                continue
            evidence_class = (
                "scientific-methodology"
                if stem == "phonon-tc-efficiency"
                and title != "Keep official capabilities distinct from experience"
                else "repository-policy"
            )
            subjects.append(
                {
                    "subject_id": f"section:{safe_id(stem)}:{safe_id(title.lower())}",
                    "subject_kind": "workflow",
                    "evidence_class": evidence_class,
                    "origin_refs": [source_ref],
                    "statement": f"The Skill declares the section-level contract: {title}.",
                    "expected_disposition": "not-applicable",
                    "provider_input_ids": [],
                }
            )
    return subjects


def literal_subcommands(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    commands: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_parser"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            commands.add(node.args[0].value)
    return tuple(sorted(commands))


def command_subjects(root: Path) -> list[dict[str, Any]]:
    relative = f"skills/{SKILL_ID}/scripts/campaign_efficiency/cli.py"
    source_ref = origin(root, relative)
    return [
        {
            "subject_id": f"cli:{command}",
            "subject_kind": "task",
            "evidence_class": "deterministic-tool-behavior",
            "origin_refs": [source_ref],
            "statement": f"The campaign CLI exposes the {command!r} subcommand.",
            "expected_disposition": "not-applicable",
            "provider_input_ids": [],
        }
        for command in literal_subcommands(root / relative)
    ]


QE_SUBJECTS = (
    ("qe:ph:start-q", "input-keyword", "`start_q` selects the first q point."),
    ("qe:ph:last-q", "input-keyword", "`last_q` selects the last q point."),
    ("qe:ph:only-init", "input-keyword", "`only_init` performs PH initialization work."),
    ("qe:ph:recover", "input-keyword", "`recover` restarts interrupted PH work."),
    (
        "qe:ph:trans-false",
        "input-keyword",
        "`trans=.false.` reuses saved response data for later EPC work.",
    ),
    ("qe:ph:lqdir", "input-keyword", "`lqdir` selects q-specific storage."),
    (
        "qe:ph:lshift-q",
        "input-keyword",
        "`lshift_q` selects the shifted-q optimized-tetrahedron route.",
    ),
    (
        "qe:ph:electron-phonon",
        "input-keyword",
        "`electron_phonon` selects QE electron-phonon behavior.",
    ),
    (
        "qe:q2r:shifted-grid-limit",
        "limitation",
        "The shifted-q optimized-tetrahedron route is incompatible with q2r.",
    ),
    (
        "qe:epw:coarse-fine-restart-artifacts",
        "workflow",
        "EPW distinguishes coarse and fine meshes and has version-sensitive restart and reusable-artifact contracts.",
    ),
)


def provider_subjects(root: Path) -> list[dict[str, Any]]:
    relative = f"skills/{SKILL_ID}/references/phonon-tc-efficiency.md"
    source_ref = origin(root, relative)
    result: list[dict[str, Any]] = []
    for subject_id, subject_kind, statement in QE_SUBJECTS:
        result.append(
            {
                "subject_id": subject_id,
                "subject_kind": subject_kind,
                "evidence_class": "official-provider-required",
                "origin_refs": [source_ref],
                "statement": statement,
                "expected_disposition": (
                    "blocked" if subject_id.startswith("qe:epw:") else "partial"
                ),
                "provider_input_ids": ["qe-phonon-epw"],
            }
        )
    return result


def scope_catalog(root: Path) -> dict[str, Any]:
    subjects = heading_subjects(root) + command_subjects(root) + provider_subjects(root)
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
    sha256: str,
    size: int,
    subject_ids: Iterable[str],
    loss_ids: Iterable[str] = (),
    retrieval_method: str = "https-get",
) -> dict[str, Any]:
    selected_subjects = sorted(set(subject_ids))
    selected_losses = sorted(set(loss_ids))
    return {
        "source_id": source_id,
        "title": title,
        "source_kind": source_kind,
        "locator": locator,
        "disposition": "included",
        "external_identity": {
            "kind": "revision",
            "value": QE_COMMIT,
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
                    "retrieval_method": retrieval_method,
                    "retrieved_utc": RETRIEVED_UTC,
                    "raw_sha256": sha256,
                    "raw_bytes": size,
                    "selected_sha256": sha256,
                    "selected_bytes": size,
                },
                "subject_ids": selected_subjects,
                "loss_ids": selected_losses,
            }
        ],
    }


def legacy_qe_catalog() -> dict[str, Any]:
    ph_subjects = [item[0] for item in QE_SUBJECTS if item[0].startswith("qe:ph:")]
    return {
        "schema_version": "1.0",
        "contract_name": "official-document-source-catalog",
        "version_scope": {
            "kind": "exact",
            "value": "7.5",
            "retrieved_utc": None,
            "snapshot_identity": None,
        },
        "upstream_universe_complete": False,
        "inventory_locator": (
            f"https://gitlab.com/QEF/q-e/-/tree/{QE_COMMIT}/PHonon/Doc"
        ),
        "sources": [
            external_source(
                source_id="qe75-input-ph",
                title="Quantum ESPRESSO 7.5 INPUT_PH",
                source_kind="reference-page",
                locator=(
                    f"https://gitlab.com/QEF/q-e/-/raw/{QE_COMMIT}/"
                    "PHonon/Doc/INPUT_PH.html"
                ),
                sha256="419948c44e7695ddc70100070a39524b0bebbb70e07561ac3f39fc2cece9ff39",
                size=96464,
                subject_ids=ph_subjects,
            ),
            external_source(
                source_id="qe75-phonon-guide",
                title="Quantum ESPRESSO 7.5 PHonon user guide",
                source_kind="pdf",
                locator=(
                    f"https://gitlab.com/QEF/q-e/-/raw/{QE_COMMIT}/"
                    "PHonon/Doc/user_guide.pdf"
                ),
                sha256="aed53913042c2732172137194ca7e86aba3ce301665d15d79c2720b1bc146f60",
                size=239679,
                subject_ids=["qe:q2r:shifted-grid-limit"],
            ),
            external_source(
                source_id="qe75-epw-readme",
                title="EPW 5.9 README distributed with Quantum ESPRESSO 7.5",
                source_kind="source-documentation",
                locator=(
                    f"https://gitlab.com/QEF/q-e/-/raw/{QE_COMMIT}/EPW/README"
                ),
                sha256="4224848ee2a2ba4556cadb2fd8235c8a514813ff56f105577e0c853e2d224fc5",
                size=4403,
                subject_ids=["qe:epw:coarse-fine-restart-artifacts"],
                loss_ids=["epw-exact-input-docs-unbound"],
            ),
        ],
        "subjects": [
            {
                "subject_id": subject_id,
                "title": statement,
                "category": (
                    "input-parameter"
                    if subject_kind == "input-keyword"
                    else "scientific-limitation"
                    if subject_kind == "limitation"
                    else "workflow"
                ),
                "requirement_strength": "required",
                "evidence_class": "official-provider-required",
            }
            for subject_id, subject_kind, statement in QE_SUBJECTS
        ],
        "reviewed_exclusions": [],
        "losses": [
            {
                "loss_id": "epw-exact-input-docs-unbound",
                "stage": "discovery",
                "description": (
                    "The QE 7.5 release tree identifies EPW 5.9, but this seed does "
                    "not yet bind an exact complete EPW input-documentation corpus."
                ),
                "materiality": "material",
                "disposition": "blocked",
                "affected_source_ids": ["qe75-epw-readme"],
            }
        ],
        "license": {
            "identity": {
                "identifier": "GPL-2.0-or-later",
                "terms_urls": [
                    f"https://gitlab.com/QEF/q-e/-/raw/{QE_COMMIT}/License"
                ],
                "verification": "unverified",
            },
            "assessment": "conditional",
            "allowed_storage_modes": ["metadata-only"],
            "official_terms_locator": (
                f"https://gitlab.com/QEF/q-e/-/raw/{QE_COMMIT}/License"
            ),
            "limitations": [
                "Only external identities and receipts are stored; no official text is embedded."
            ],
        },
        "limitations": [
            "The selected PH and EPW sources do not enumerate the complete QE documentation universe."
        ],
        "blockers": [
            {
                "code": "epw-exact-documentation-unbound",
                "description": (
                    "Exact EPW mesh, restart, and Eliashberg-artifact documentation "
                    "has not been enumerated and content-bound."
                ),
                "dimensions": ["corpus", "slices"],
            }
        ],
    }


PROVIDER = {
    "input_id": "qe-phonon-epw",
    "adapter_id": "declarative-catalog-v1",
    "authority_id": "qe-release-source-docs",
    "provider_id": "qe",
}


def authority_projection(root: Path) -> dict[str, Any]:
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
            "central authority projection is invalid: "
            + " | ".join(str(item) for item in failures)
        )
    authority_id = PROVIDER["authority_id"]
    if authority_id not in projections:
        raise ValueError(f"central authority projection is missing {authority_id}")
    return projections[authority_id]


def qe_catalog(
    root: Path,
    *,
    scope: dict[str, Any] | None = None,
) -> dict[str, Any]:
    legacy = legacy_qe_catalog()
    legacy_bytes = canonical_json_bytes(legacy)
    included = [
        source
        for source in legacy["sources"]
        if source.get("disposition") == "included"
    ]
    if not included:
        raise ValueError("legacy QE catalog has no included source")
    return convert_catalog_v10_to_v11(
        legacy,
        provider=PROVIDER,
        authority={"authority_id": PROVIDER["authority_id"]},
        authority_projection=authority_projection(root),
        scope_catalog=scope if scope is not None else scope_catalog(root),
        inventory_projection={
            "locator": included[0]["locator"],
            "identity": {
                "sha256": sha256_bytes(legacy_bytes),
                "bytes": len(legacy_bytes),
            },
            "canonical_preimage_bytes": legacy_bytes,
        },
    )


def authority_proposal() -> dict[str, Any]:
    """Return the central-registry proposal without changing central state."""

    return {
        "schema_version": "1.0",
        "proposal_type": "official-source-authority-and-consumer-bindings",
        "skill_id": SKILL_ID,
        "lifecycle_effect": "none",
        "authorities": [],
        "existing_authority_bindings": [
            {
                "authority_id": "qe-release-source-docs",
                "provider_class": "software",
                "provider_id": "qe",
                "consumer_binding": {
                    "binding_id": "dft-campaign-efficiency-qe-release-source",
                    "consumer_skill_id": SKILL_ID,
                    "consumer_lifecycle": "active",
                    "consumer_path": f"skills/{SKILL_ID}",
                    "authority_id": "qe-release-source-docs",
                    "provider_id": "qe",
                    "purpose": "official-document-coverage",
                    "claim_ceiling": "registered-skill-scope",
                },
            }
        ],
        "provider_registry_proposals": [],
        "central_blockers": [
            "Add the consumer binding before running the production pack builder."
        ],
        "invariants": [
            "The proposal does not change Skill/software lifecycle, routing, installability, execution permission, or claim ceiling.",
            "The binding permits coverage measurement only; it does not establish EPW completeness or scientific acceptance.",
        ],
    }


def build_outputs(root: Path) -> dict[Path, bytes]:
    skill_root = root / "skills" / SKILL_ID
    scope_path = skill_root / "references" / "source-pack-scope.json"
    provider_path = (
        skill_root / "references" / "source-pack-inputs" / "qe-phonon-epw.json"
    )
    scope = scope_catalog(root)
    scope_bytes = canonical_json_bytes(scope)
    provider_bytes = canonical_json_bytes(qe_catalog(root, scope=scope))
    seed = {
        "schema_version": "1.0",
        "contract_name": "official-document-pack-seed",
        "skill_id": SKILL_ID,
        "status_ceiling": "blocked",
        "scope_extractor_id": "dft-campaign-efficiency-scope-v1",
        "scope_catalog_ref": {
            "path": scope_path.relative_to(root).as_posix(),
            "sha256": sha256_bytes(scope_bytes),
        },
        "providers": [
            {
                **PROVIDER,
                "source_ref": {
                    "path": provider_path.relative_to(root).as_posix(),
                    "sha256": sha256_bytes(provider_bytes),
                },
            }
        ],
        "limitations": [
            "This production seed stores metadata and receipts only and cannot assert complete coverage."
        ],
        "blockers": [
            "Exact EPW mesh, restart, and reusable-artifact documentation remains unbound."
        ],
    }
    return {
        scope_path: scope_bytes,
        provider_path: provider_bytes,
        (
            skill_root
            / "references"
            / "source-pack-authority-proposal.json"
        ): canonical_json_bytes(authority_proposal()),
        skill_root / "references" / "source-pack-seed.json": canonical_json_bytes(seed),
    }


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
