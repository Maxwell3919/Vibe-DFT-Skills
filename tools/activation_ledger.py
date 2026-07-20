#!/usr/bin/env python3
"""Validate active lifecycle activation and maturity ledgers fail closed."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any, Sequence

from registry_yaml import RegistryYAMLError, load_yaml_strict
from skill_registry import source_tree_digest


SHA256 = re.compile(r"^[a-f0-9]{64}$")
ACTIVATION_STATES = frozenset(
    {"legacy-active-review-required", "approved", "revoked", "superseded"}
)
REVIEW_STATES = frozenset({"current", "review-required", "stale", "blocked"})
MATURITY_STATES = frozenset(
    {
        "not-assessed",
        "design-only",
        "synthetic-validated",
        "format-fixture-validated",
        "real-artifact-validated",
        "tool-integration-validated",
        "validated",
    }
)
CLAIM_ORDER = {
    "no_positive_claim": 0,
    "documented_behavior_only": 1,
    "input_gates_only": 2,
    "technical_run_gates_only": 3,
    "numerical_candidate_only": 4,
    "eligible_for_expert_review": 5,
}
EXPECTED_DIMENSIONS = (
    "skill",
    "software",
    "software-version",
    "executable",
    "task",
    "observable",
    "backend",
    "platform",
)
REQUIRED_REVIEW_TRIGGERS = frozenset(
    {
        "software-major-or-minor-version-change",
        "executable-or-output-format-change",
        "parser-or-normalization-change",
        "contract-major-version-change",
        "fixture-bytes-or-provenance-change",
        "backend-change",
        "unit-or-reference-energy-semantics-change",
        "dependency-major-version-change",
        "official-source-authority-change",
        "privacy-or-redistribution-change",
        "authorization-or-side-effect-change",
    }
)


@dataclass(frozen=True, order=True)
class Finding:
    code: str
    location: str
    message: str

    def render(self) -> str:
        return f"{self.code}\t{self.location}\t{self.message}"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load(path: Path, label: str) -> tuple[dict[str, Any] | None, list[Finding]]:
    try:
        value = load_yaml_strict(path)
    except (OSError, UnicodeError, RegistryYAMLError) as exc:
        return None, [Finding("LEDGER_UNREADABLE", label, str(exc))]
    if not isinstance(value, dict) or value.get("schema_version") != "1.0":
        return None, [
            Finding("LEDGER_SCHEMA_INVALID", label, "schema_version must be 1.0")
        ]
    return value, []


def _safe_path(root: Path, value: object) -> Path | None:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        return None
    relative = PurePosixPath(value)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        return None
    path = root.joinpath(*relative.parts)
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return path


def _active_skills(root: Path) -> tuple[dict[str, dict[str, Any]], list[Finding]]:
    registry, findings = _load(
        root / "registry" / "skill-registry.yaml",
        "registry/skill-registry.yaml",
    )
    if registry is None:
        return {}, findings
    skills = registry.get("skills")
    if not isinstance(skills, dict):
        return {}, findings + [
            Finding(
                "LEDGER_SKILL_REGISTRY_INVALID",
                "registry/skill-registry.yaml/skills",
                "skills must be a mapping",
            )
        ]
    active: dict[str, dict[str, Any]] = {}
    for name, specification in skills.items():
        if (
            isinstance(name, str)
            and isinstance(specification, dict)
            and specification.get("lifecycle") == "active"
        ):
            active[name] = specification
    if not active:
        findings.append(
            Finding(
                "LEDGER_ACTIVE_SET_EMPTY",
                "registry/skill-registry.yaml",
                "no active Skills are registered",
            )
        )
    return active, findings


def validate_activation(
    root: Path,
    active: dict[str, dict[str, Any]],
) -> list[Finding]:
    ledger, findings = _load(
        root / "registry" / "activation-ledger.yaml",
        "registry/activation-ledger.yaml",
    )
    if ledger is None:
        return findings
    for field in ("ledger_id", "baseline_source_commit", "governance_commit"):
        value = ledger.get(field)
        if not isinstance(value, str) or not value:
            findings.append(
                Finding(
                    "ACTIVATION_LEDGER_IDENTITY_INVALID",
                    f"registry/activation-ledger.yaml/{field}",
                    "required identity field is missing",
                )
            )
    records = ledger.get("records")
    if not isinstance(records, dict):
        return findings + [
            Finding(
                "ACTIVATION_RECORDS_INVALID",
                "registry/activation-ledger.yaml/records",
                "records must be a mapping",
            )
        ]
    if set(records) != set(active):
        findings.append(
            Finding(
                "ACTIVATION_ACTIVE_SET_MISMATCH",
                "registry/activation-ledger.yaml/records",
                f"ledger={sorted(records)} active={sorted(active)}",
            )
        )

    for name in sorted(set(records).intersection(active)):
        record = records[name]
        location = f"registry/activation-ledger.yaml/records/{name}"
        if not isinstance(record, dict):
            findings.append(
                Finding("ACTIVATION_RECORD_INVALID", location, "record must be a mapping")
            )
            continue
        if record.get("lifecycle") != "active":
            findings.append(
                Finding("ACTIVATION_LIFECYCLE_INVALID", location, "lifecycle must be active")
            )
        state = record.get("activation_state")
        if state not in ACTIVATION_STATES:
            findings.append(
                Finding(
                    "ACTIVATION_STATE_INVALID",
                    location,
                    f"invalid activation state {state!r}",
                )
            )
        expected_hash = active[name].get("source_tree_sha256")
        declared_hash = record.get("source_tree_sha256")
        if (
            not isinstance(declared_hash, str)
            or SHA256.fullmatch(declared_hash) is None
            or declared_hash != expected_hash
        ):
            findings.append(
                Finding(
                    "ACTIVATION_SOURCE_HASH_MISMATCH",
                    f"{location}/source_tree_sha256",
                    "activation source hash must equal the active Skill registry",
                )
            )
        path_text = active[name].get("path")
        source = _safe_path(root, path_text)
        if source is None or not source.is_dir():
            findings.append(
                Finding(
                    "ACTIVATION_SOURCE_PATH_INVALID",
                    f"{location}/source_tree_sha256",
                    "active Skill source path is missing or unsafe",
                )
            )
        else:
            try:
                actual_hash = source_tree_digest(source).sha256
            except ValueError as exc:
                findings.append(
                    Finding(
                        "ACTIVATION_SOURCE_TREE_INVALID",
                        f"{location}/source_tree_sha256",
                        str(exc),
                    )
                )
            else:
                if actual_hash != declared_hash:
                    findings.append(
                        Finding(
                            "ACTIVATION_SOURCE_BYTES_MISMATCH",
                            f"{location}/source_tree_sha256",
                            "recorded hash does not match current source bytes",
                        )
                    )
        baseline = _safe_path(root, record.get("baseline_record"))
        if baseline is None or not baseline.is_file():
            findings.append(
                Finding(
                    "ACTIVATION_BASELINE_RECORD_MISSING",
                    f"{location}/baseline_record",
                    "baseline record must be a safe existing file",
                )
            )
        independent = record.get("independent_promotion_evidence")
        native = record.get("native_execution_claimed")
        science = record.get("scientific_acceptance_claimed")
        if not all(isinstance(value, bool) for value in (independent, native, science)):
            findings.append(
                Finding(
                    "ACTIVATION_CLAIM_FLAGS_INVALID",
                    location,
                    "activation claim flags must be boolean",
                )
            )
        if state == "legacy-active-review-required" and any(
            value is not False for value in (independent, native, science)
        ):
            findings.append(
                Finding(
                    "ACTIVATION_LEGACY_CLAIM_OVERSTATED",
                    location,
                    "legacy active records cannot claim independent, native, or scientific evidence",
                )
            )
        if state == "approved" and independent is not True:
            findings.append(
                Finding(
                    "ACTIVATION_APPROVAL_EVIDENCE_MISSING",
                    location,
                    "approved activation requires independent promotion evidence",
                )
            )
        actions = record.get("required_next_actions")
        if (
            not isinstance(actions, list)
            or not actions
            or any(not isinstance(item, str) or not item for item in actions)
            or len(actions) != len(set(actions))
        ):
            findings.append(
                Finding(
                    "ACTIVATION_NEXT_ACTIONS_INVALID",
                    f"{location}/required_next_actions",
                    "required next actions must be a nonempty unique string list",
                )
            )
    return findings


def validate_maturity(
    root: Path,
    active: dict[str, dict[str, Any]],
) -> list[Finding]:
    ledger, findings = _load(
        root / "registry" / "maturity-ledger.yaml",
        "registry/maturity-ledger.yaml",
    )
    if ledger is None:
        return findings
    if not isinstance(ledger.get("ledger_id"), str) or not ledger["ledger_id"]:
        findings.append(
            Finding(
                "MATURITY_LEDGER_ID_INVALID",
                "registry/maturity-ledger.yaml/ledger_id",
                "ledger_id is required",
            )
        )
    entries = ledger.get("entries")
    if not isinstance(entries, dict):
        return findings + [
            Finding(
                "MATURITY_ENTRIES_INVALID",
                "registry/maturity-ledger.yaml/entries",
                "entries must be a mapping",
            )
        ]
    if set(entries) != set(active):
        findings.append(
            Finding(
                "MATURITY_ACTIVE_SET_MISMATCH",
                "registry/maturity-ledger.yaml/entries",
                f"ledger={sorted(entries)} active={sorted(active)}",
            )
        )
    for name in sorted(set(entries).intersection(active)):
        entry = entries[name]
        location = f"registry/maturity-ledger.yaml/entries/{name}"
        if not isinstance(entry, dict):
            findings.append(
                Finding("MATURITY_ENTRY_INVALID", location, "entry must be a mapping")
            )
            continue
        if entry.get("lifecycle") != "active":
            findings.append(
                Finding("MATURITY_LIFECYCLE_INVALID", location, "lifecycle must be active")
            )
        if entry.get("review_status") not in REVIEW_STATES:
            findings.append(
                Finding(
                    "MATURITY_REVIEW_STATUS_INVALID",
                    location,
                    f"invalid review status {entry.get('review_status')!r}",
                )
            )
        catalog = _safe_path(root, entry.get("route_catalog"))
        if catalog is None or not catalog.is_file():
            findings.append(
                Finding(
                    "MATURITY_ROUTE_CATALOG_MISSING",
                    f"{location}/route_catalog",
                    "route catalog must be a safe existing file",
                )
            )
        dimensions = entry.get("dimensions")
        if dimensions != list(EXPECTED_DIMENSIONS):
            findings.append(
                Finding(
                    "MATURITY_DIMENSIONS_INVALID",
                    f"{location}/dimensions",
                    f"dimensions must be exactly {list(EXPECTED_DIMENSIONS)}",
                )
            )
        for field in ("repository_behavior", "native_execution", "scientific_validation"):
            if entry.get(field) not in MATURITY_STATES:
                findings.append(
                    Finding(
                        "MATURITY_AXIS_INVALID",
                        f"{location}/{field}",
                        f"invalid maturity value {entry.get(field)!r}",
                    )
                )
        ceiling = entry.get("claim_ceiling")
        if ceiling not in CLAIM_ORDER:
            findings.append(
                Finding(
                    "MATURITY_CLAIM_CEILING_INVALID",
                    f"{location}/claim_ceiling",
                    f"invalid claim ceiling {ceiling!r}",
                )
            )
        elif (
            entry.get("native_execution") == "not-assessed"
            or entry.get("scientific_validation") == "not-assessed"
        ) and CLAIM_ORDER[ceiling] > CLAIM_ORDER["documented_behavior_only"]:
            findings.append(
                Finding(
                    "MATURITY_CLAIM_CEILING_OVERSTATED",
                    f"{location}/claim_ceiling",
                    "unassessed native/scientific axes cap claims at documented behavior",
                )
            )
        scope = entry.get("version_scope")
        if not isinstance(scope, list) or any(
            not isinstance(item, str) or not item for item in scope
        ):
            findings.append(
                Finding(
                    "MATURITY_VERSION_SCOPE_INVALID",
                    f"{location}/version_scope",
                    "version_scope must be a string list",
                )
            )
    triggers = ledger.get("automatic_review_triggers")
    if not isinstance(triggers, list) or set(triggers) != REQUIRED_REVIEW_TRIGGERS:
        findings.append(
            Finding(
                "MATURITY_REVIEW_TRIGGERS_INVALID",
                "registry/maturity-ledger.yaml/automatic_review_triggers",
                "automatic review triggers are incomplete or contain extras",
            )
        )
    return findings


def audit(root: Path) -> list[Finding]:
    active, findings = _active_skills(root)
    findings.extend(validate_activation(root, active))
    findings.extend(validate_maturity(root, active))
    return sorted(set(findings))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root())
    args = parser.parse_args(argv)
    findings = audit(args.root.resolve())
    if findings:
        for finding in findings:
            print(finding.render(), file=sys.stderr)
        return 2
    print("PASS: activation and maturity ledgers match every active Skill")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
