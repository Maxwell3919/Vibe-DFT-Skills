#!/usr/bin/env python3
"""Validate canonical active-Skill evidence truth without inventing promotion history."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any, Iterable, Sequence

sys.dont_write_bytecode = True

from registry_yaml import RegistryYAMLError, load_yaml_strict
from skill_registry import source_tree_digest
import strict_json
import validate_contract
import validate_promotion


SCHEMA_VERSION = "1.0"
SHA256 = re.compile(r"^[a-f0-9]{64}$")
COMMIT = re.compile(r"^[a-f0-9]{40}$")
SKILL_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ACTIVATION_EVIDENCE_STATUSES = frozenset({"legacy-unclosed", "verified"})
RECORD_FIELDS = frozenset(
    {
        "skill_id",
        "lifecycle",
        "source_tree_sha256",
        "activation_evidence_status",
        "promotion_evidence",
        "route_maturity_refs",
        "context_refs",
        "known_limitations",
        "closure_requirements",
        "prohibited_claims",
    }
)
REF_FIELDS = frozenset({"path", "sha256", "scope"})
PROMOTION_REF_FIELDS = (
    "activation_record",
    "task_maturity_catalog",
    "promotion_delta",
    "validation_report",
)
REQUIRED_LEGACY_PROHIBITED_CLAIMS = frozenset(
    {
        "independent-activation-review-complete",
        "active-lifecycle-evidence-closed",
        "aggregate-maturity-upgraded-from-activation-status",
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


def load_registry(path: Path | None = None) -> dict[str, Any]:
    selected = path or repo_root() / "registry" / "active-evidence.yaml"
    return load_yaml_strict(selected, selected.name)


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


def _string_list(
    value: object,
    location: str,
    findings: list[Finding],
    *,
    allow_empty: bool,
) -> list[str]:
    if (
        not isinstance(value, list)
        or (not allow_empty and not value)
        or any(not isinstance(item, str) or not item.strip() for item in value)
        or len(value) != len(set(value))
    ):
        findings.append(
            Finding(
                "ACTIVE_EVIDENCE_STRING_LIST_INVALID",
                location,
                "expected a unique string list",
            )
        )
        return []
    return value


def _active_skills(skill_data: object) -> dict[str, dict[str, Any]]:
    if not isinstance(skill_data, dict) or not isinstance(skill_data.get("skills"), dict):
        return {}
    return {
        name: specification
        for name, specification in skill_data["skills"].items()
        if isinstance(name, str)
        and isinstance(specification, dict)
        and specification.get("lifecycle") == "active"
    }


def _validate_ref(
    reference: object,
    *,
    root: Path,
    location: str,
    findings: list[Finding],
) -> tuple[Path | None, bytes | None]:
    if not isinstance(reference, dict) or set(reference) != REF_FIELDS:
        findings.append(
            Finding(
                "ACTIVE_EVIDENCE_REF_INVALID",
                location,
                f"expected fields {sorted(REF_FIELDS)!r}",
            )
        )
        return None, None
    scope = reference.get("scope")
    if not isinstance(scope, str) or not scope.strip():
        findings.append(
            Finding(
                "ACTIVE_EVIDENCE_REF_SCOPE_INVALID",
                f"{location}/scope",
                "scope must be a nonempty string",
            )
        )
    path = _safe_path(root, reference.get("path"))
    if path is None:
        findings.append(
            Finding(
                "ACTIVE_EVIDENCE_REF_PATH_INVALID",
                f"{location}/path",
                "expected a safe repository-relative path",
            )
        )
        return None, None
    if path.is_symlink() or not path.is_file():
        findings.append(
            Finding(
                "ACTIVE_EVIDENCE_REF_MISSING",
                f"{location}/path",
                "referenced evidence file is missing or aliased",
            )
        )
        return path, None
    try:
        raw = path.read_bytes()
    except OSError as exc:
        findings.append(
            Finding(
                "ACTIVE_EVIDENCE_REF_MISSING",
                f"{location}/path",
                f"cannot read referenced evidence: {exc.__class__.__name__}",
            )
        )
        return path, None
    declared_hash = reference.get("sha256")
    actual_hash = hashlib.sha256(raw).hexdigest()
    if (
        not isinstance(declared_hash, str)
        or SHA256.fullmatch(declared_hash) is None
        or declared_hash != actual_hash
    ):
        findings.append(
            Finding(
                "ACTIVE_EVIDENCE_REF_HASH_MISMATCH",
                f"{location}/sha256",
                "declared SHA-256 does not match referenced bytes",
            )
        )
    return path, raw


def _json_object(
    raw: bytes | None,
    *,
    location: str,
    findings: list[Finding],
) -> dict[str, Any] | None:
    if raw is None:
        return None
    try:
        return strict_json.loads_object(raw, location)
    except strict_json.StrictJSONError as exc:
        findings.append(
            Finding(
                "ACTIVE_EVIDENCE_VERIFIED_ARTIFACT_INVALID",
                location,
                str(exc),
            )
        )
        return None


def _contract_findings(
    selector: str,
    value: dict[str, Any] | None,
    *,
    root: Path,
    location: str,
) -> list[Finding]:
    if value is None:
        return []
    return [
        Finding("ACTIVE_EVIDENCE_VERIFIED_ARTIFACT_INVALID", location, error)
        for error in validate_contract.validation_errors(
            selector,
            value,
            root / "contracts",
        )
    ]


def _validate_verified_promotion(
    promotion_evidence: object,
    *,
    root: Path,
    skill_id: str,
    source_tree_sha256: object,
    location: str,
    findings: list[Finding],
) -> None:
    if (
        not isinstance(promotion_evidence, dict)
        or set(promotion_evidence) != set(PROMOTION_REF_FIELDS)
    ):
        findings.append(
            Finding(
                "ACTIVE_EVIDENCE_VERIFIED_REFS_MISSING",
                location,
                f"verified status requires {list(PROMOTION_REF_FIELDS)!r}",
            )
        )
        return

    paths: dict[str, Path | None] = {}
    values: dict[str, dict[str, Any] | None] = {}
    for field in PROMOTION_REF_FIELDS:
        paths[field], raw = _validate_ref(
            promotion_evidence.get(field),
            root=root,
            location=f"{location}/{field}",
            findings=findings,
        )
        values[field] = _json_object(
            raw,
            location=f"{location}/{field}",
            findings=findings,
        )

    findings.extend(
        _contract_findings(
            "activation-checklist@1.1",
            values["activation_record"],
            root=root,
            location=f"{location}/activation_record",
        )
    )
    findings.extend(
        _contract_findings(
            "task-maturity@1.1",
            values["task_maturity_catalog"],
            root=root,
            location=f"{location}/task_maturity_catalog",
        )
    )
    findings.extend(
        _contract_findings(
            "promotion-delta@1.1",
            values["promotion_delta"],
            root=root,
            location=f"{location}/promotion_delta",
        )
    )

    activation = values["activation_record"] or {}
    maturity = values["task_maturity_catalog"] or {}
    promotion = values["promotion_delta"] or {}
    report = values["validation_report"] or {}
    candidate = promotion.get("candidate_commit")
    promotion_id = promotion.get("promotion_id")
    expected_report = {
        "validator": "two-phase-promotion-validator",
        "skill_id": skill_id,
        "promotion_id": promotion_id,
        "candidate_commit": candidate,
        "status": "pass",
        "eligible": True,
        "finding_count": 0,
        "findings": [],
    }
    mismatches = [
        field
        for field, expected in expected_report.items()
        if report.get(field) != expected
    ]
    if report.get("schema_version") != "1.0" or mismatches:
        findings.append(
            Finding(
                "ACTIVE_EVIDENCE_VERIFICATION_REPORT_INVALID",
                f"{location}/validation_report",
                f"invalid or mismatched fields {sorted(mismatches)!r}",
            )
        )
    if not isinstance(report.get("review_commit"), str) or COMMIT.fullmatch(
        report["review_commit"]
    ) is None:
        findings.append(
            Finding(
                "ACTIVE_EVIDENCE_VERIFICATION_REPORT_INVALID",
                f"{location}/validation_report/review_commit",
                "review_commit must be a full Git commit SHA",
            )
        )
    subject = activation.get("subject")
    if (
        not isinstance(subject, dict)
        or subject.get("skill_id") != skill_id
        or subject.get("candidate_commit") != candidate
        or maturity.get("skill_id") != skill_id
        or promotion.get("skill_id") != skill_id
    ):
        findings.append(
            Finding(
                "ACTIVE_EVIDENCE_VERIFIED_SUBJECT_MISMATCH",
                location,
                "promotion artifacts do not bind the same Skill and candidate commit",
            )
        )
    path_transition = promotion.get("path_transition")
    if (
        not isinstance(path_transition, dict)
        or path_transition.get("source_tree_sha256") != source_tree_sha256
    ):
        findings.append(
            Finding(
                "ACTIVE_EVIDENCE_VERIFIED_SOURCE_MISMATCH",
                f"{location}/promotion_delta",
                "verified promotion source identity does not match the active source",
            )
        )
    promotion_path = paths["promotion_delta"]
    review_commit = report.get("review_commit")
    if promotion_path is not None and isinstance(review_commit, str):
        rerun_findings, rerun_report = validate_promotion.validate_promotion(
            root,
            promotion_path,
            review_commit=review_commit,
            contracts_dir=root / "contracts",
        )
        if rerun_findings or rerun_report != report:
            findings.append(
                Finding(
                    "ACTIVE_EVIDENCE_VERIFICATION_REPLAY_FAILED",
                    f"{location}/validation_report",
                    "stored validation report does not match an independent promotion replay",
                )
            )


def validation_findings(
    data: object,
    *,
    root: Path | None = None,
    skill_data: object,
    validate_sources: bool = True,
) -> list[Finding]:
    selected_root = (root or repo_root()).resolve()
    findings: list[Finding] = []
    if not isinstance(data, dict):
        return [
            Finding(
                "ACTIVE_EVIDENCE_REGISTRY_INVALID",
                "<root>",
                "registry must be a mapping",
            )
        ]
    expected_root_fields = {"schema_version", "registry_id", "records"}
    if set(data) != expected_root_fields or data.get("schema_version") != SCHEMA_VERSION:
        findings.append(
            Finding(
                "ACTIVE_EVIDENCE_REGISTRY_INVALID",
                "<root>",
                f"expected schema {SCHEMA_VERSION} and fields {sorted(expected_root_fields)!r}",
            )
        )
    if not isinstance(data.get("registry_id"), str) or not data["registry_id"].strip():
        findings.append(
            Finding(
                "ACTIVE_EVIDENCE_REGISTRY_INVALID",
                "registry_id",
                "registry_id must be a nonempty string",
            )
        )

    active = _active_skills(skill_data)
    if not active:
        findings.append(
            Finding(
                "ACTIVE_EVIDENCE_SKILL_REGISTRY_INVALID",
                "registry/skill-registry.yaml",
                "no active Skills are available for cross-validation",
            )
        )
    records = data.get("records")
    if not isinstance(records, dict):
        return sorted(
            set(
                findings
                + [
                    Finding(
                        "ACTIVE_EVIDENCE_RECORDS_INVALID",
                        "records",
                        "records must be a mapping",
                    )
                ]
            )
        )
    if set(records) != set(active):
        findings.append(
            Finding(
                "ACTIVE_EVIDENCE_SET_MISMATCH",
                "records",
                f"evidence={sorted(records)!r} active={sorted(active)!r}",
            )
        )

    for name in sorted(set(records).intersection(active)):
        record = records[name]
        location = f"records/{name}"
        if not isinstance(name, str) or SKILL_ID.fullmatch(name) is None:
            findings.append(
                Finding(
                    "ACTIVE_EVIDENCE_SKILL_ID_INVALID",
                    location,
                    "invalid Skill identifier",
                )
            )
        if not isinstance(record, dict) or set(record) != RECORD_FIELDS:
            findings.append(
                Finding(
                    "ACTIVE_EVIDENCE_RECORD_INVALID",
                    location,
                    f"expected fields {sorted(RECORD_FIELDS)!r}",
                )
            )
            continue
        if record.get("skill_id") != name:
            findings.append(
                Finding(
                    "ACTIVE_EVIDENCE_SKILL_ID_MISMATCH",
                    f"{location}/skill_id",
                    "record Skill ID must equal its mapping key",
                )
            )
        if record.get("lifecycle") != "active":
            findings.append(
                Finding(
                    "ACTIVE_EVIDENCE_LIFECYCLE_MISMATCH",
                    f"{location}/lifecycle",
                    "evidence record must describe the active lifecycle",
                )
            )
        registered_hash = active[name].get("source_tree_sha256")
        recorded_hash = record.get("source_tree_sha256")
        if (
            not isinstance(recorded_hash, str)
            or SHA256.fullmatch(recorded_hash) is None
            or recorded_hash != registered_hash
        ):
            findings.append(
                Finding(
                    "ACTIVE_EVIDENCE_SOURCE_HASH_MISMATCH",
                    f"{location}/source_tree_sha256",
                    "evidence source hash must equal the active Skill registry",
                )
            )
        if validate_sources:
            source = _safe_path(selected_root, active[name].get("path"))
            if source is None or source.is_symlink() or not source.is_dir():
                findings.append(
                    Finding(
                        "ACTIVE_EVIDENCE_SOURCE_PATH_INVALID",
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
                            "ACTIVE_EVIDENCE_SOURCE_BYTES_INVALID",
                            f"{location}/source_tree_sha256",
                            str(exc),
                        )
                    )
                else:
                    if actual_hash != recorded_hash:
                        findings.append(
                            Finding(
                                "ACTIVE_EVIDENCE_SOURCE_BYTES_MISMATCH",
                                f"{location}/source_tree_sha256",
                                "recorded hash does not match current source bytes",
                            )
                        )

        status = record.get("activation_evidence_status")
        if status not in ACTIVATION_EVIDENCE_STATUSES:
            findings.append(
                Finding(
                    "ACTIVE_EVIDENCE_STATUS_INVALID",
                    f"{location}/activation_evidence_status",
                    f"unsupported status {status!r}",
                )
            )
        promotion_evidence = record.get("promotion_evidence")
        if status == "legacy-unclosed":
            if promotion_evidence is not None:
                findings.append(
                    Finding(
                        "ACTIVE_EVIDENCE_LEGACY_REFS_FORBIDDEN",
                        f"{location}/promotion_evidence",
                        "legacy-unclosed records cannot carry promotion evidence",
                    )
                )
        elif status == "verified":
            _validate_verified_promotion(
                promotion_evidence,
                root=selected_root,
                skill_id=name,
                source_tree_sha256=recorded_hash,
                location=f"{location}/promotion_evidence",
                findings=findings,
            )

        route_refs = record.get("route_maturity_refs")
        if not isinstance(route_refs, list) or not route_refs:
            findings.append(
                Finding(
                    "ACTIVE_EVIDENCE_ROUTE_MATURITY_REFS_INVALID",
                    f"{location}/route_maturity_refs",
                    "at least one route/task maturity reference is required",
                )
            )
        else:
            for index, reference in enumerate(route_refs):
                _validate_ref(
                    reference,
                    root=selected_root,
                    location=f"{location}/route_maturity_refs/{index}",
                    findings=findings,
                )
        context_refs = record.get("context_refs")
        if not isinstance(context_refs, list):
            findings.append(
                Finding(
                    "ACTIVE_EVIDENCE_CONTEXT_REFS_INVALID",
                    f"{location}/context_refs",
                    "context_refs must be a list",
                )
            )
        else:
            for index, reference in enumerate(context_refs):
                _validate_ref(
                    reference,
                    root=selected_root,
                    location=f"{location}/context_refs/{index}",
                    findings=findings,
                )

        _string_list(
            record.get("known_limitations"),
            f"{location}/known_limitations",
            findings,
            allow_empty=status == "verified",
        )
        _string_list(
            record.get("closure_requirements"),
            f"{location}/closure_requirements",
            findings,
            allow_empty=status == "verified",
        )
        prohibited = _string_list(
            record.get("prohibited_claims"),
            f"{location}/prohibited_claims",
            findings,
            allow_empty=status == "verified",
        )
        if status == "legacy-unclosed" and not REQUIRED_LEGACY_PROHIBITED_CLAIMS.issubset(
            prohibited
        ):
            findings.append(
                Finding(
                    "ACTIVE_EVIDENCE_LEGACY_CLAIM_BOUNDARY_INCOMPLETE",
                    f"{location}/prohibited_claims",
                    "legacy record omits a mandatory prohibited activation claim",
                )
            )
    return sorted(set(findings))


def validation_errors(
    data: object,
    *,
    root: Path | None = None,
    skill_data: object,
    validate_sources: bool = True,
) -> list[str]:
    return [
        finding.render()
        for finding in validation_findings(
            data,
            root=root,
            skill_data=skill_data,
            validate_sources=validate_sources,
        )
    ]


def legacy_skill_ids(data: dict[str, Any]) -> tuple[str, ...]:
    records = data.get("records", {})
    if not isinstance(records, dict):
        return ()
    return tuple(
        sorted(
            name
            for name, record in records.items()
            if isinstance(name, str)
            and isinstance(record, dict)
            and record.get("activation_evidence_status") == "legacy-unclosed"
        )
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry",
        type=Path,
        default=repo_root() / "registry" / "active-evidence.yaml",
    )
    parser.add_argument(
        "--skill-registry",
        type=Path,
        default=repo_root() / "registry" / "skill-registry.yaml",
    )
    parser.add_argument("--root", type=Path, default=repo_root())
    args = parser.parse_args(argv)
    try:
        data = load_registry(args.registry)
        skills = load_yaml_strict(args.skill_registry, args.skill_registry.name)
    except (OSError, UnicodeError, RegistryYAMLError) as exc:
        print(
            f"ACTIVE_EVIDENCE_REGISTRY_UNREADABLE: {exc.__class__.__name__}",
            file=sys.stderr,
        )
        return 2
    findings = validation_findings(
        data,
        root=args.root,
        skill_data=skills,
        validate_sources=True,
    )
    if findings:
        for finding in findings:
            print(finding.render(), file=sys.stderr)
        return 2
    print(
        "PASS: active evidence truth covers every active Skill; "
        f"legacy_unclosed={len(legacy_skill_ids(data))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
