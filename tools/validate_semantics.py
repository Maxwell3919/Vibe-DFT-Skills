#!/usr/bin/env python3
"""Fail-closed semantic and privacy checks for shared Vibe-DFT manifests."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Any, Iterable

import strict_json
import validate_contract


SUPPORTED_KINDS = {"run", "plan", "execution", "dataset", "artifact"}
FORBIDDEN_FIELD_NAMES = {
    "account",
    "api-key",
    "apikey",
    "credential",
    "credentials",
    "host",
    "hostname",
    "password",
    "passwd",
    "private-key",
    "secret",
    "ssh-key",
    "token",
    "user",
    "username",
}
ABSOLUTE_WINDOWS_PATH = re.compile(r"^[A-Za-z]:[\\/]")
EMBEDDED_PRIVATE_PATH = re.compile(
    r"(?:^|[=:\s])(?:/(?:Users|home|Volumes|private|tmp|var/folders)/|[A-Za-z]:[\\/])"
)
SECRET_TEXT = re.compile(
    r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\bgh[pousr]_[A-Za-z0-9_]{20,}|"
    r"\bAKIA[0-9A-Z]{16}\b|\bsk-[A-Za-z0-9_-]{20,})"
)


@dataclass(frozen=True, order=True)
class Finding:
    code: str
    location: str
    message: str

    def render(self) -> str:
        return f"{self.code} {self.location}: {self.message}"


def _location(parts: Iterable[str]) -> str:
    rendered = "/".join(parts)
    return rendered or "<root>"


def _normalized_key(value: str) -> str:
    return value.strip().lower().replace("_", "-")


def _walk(value: object, parts: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], object]]:
    yield parts, value
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk(item, (*parts, str(key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, (*parts, str(index)))


def _privacy_findings(data: object) -> list[Finding]:
    findings: list[Finding] = []
    for parts, value in _walk(data):
        location = _location(parts)
        if parts and _normalized_key(parts[-1]) in FORBIDDEN_FIELD_NAMES:
            findings.append(
                Finding("privacy-forbidden-field", location, "private identity or credential fields are forbidden")
            )
        if not isinstance(value, str):
            continue
        if (
            value.startswith(("/", "~", "file://", "\\\\"))
            or ABSOLUTE_WINDOWS_PATH.match(value)
            or EMBEDDED_PRIVATE_PATH.search(value)
        ):
            findings.append(Finding("privacy-absolute-path", location, "store a safe label or repository-relative path"))
        normalized = value.replace("\\", "/")
        if any(part == ".." for part in normalized.split("/")):
            findings.append(Finding("privacy-path-traversal", location, "parent-directory traversal is forbidden"))
        if SECRET_TEXT.search(value):
            findings.append(Finding("privacy-secret-text", location, "credential-like text is forbidden"))
    return findings


def _run_findings(data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    status = data.get("status")
    acceptance = data.get("scientific_acceptance")
    if status == "completed" and acceptance not in {
        "not_assessed",
        "requires_human_review",
    }:
        findings.append(
            Finding(
                "run-predecision-ceiling-exceeded",
                "scientific_acceptance",
                "completed runs may be unassessed or ready for human review, never self-accepted or self-rejected",
            )
        )
    if status in {"planned", "running", "stopped", "failed"} and acceptance != "not_assessed":
        findings.append(
            Finding(
                "run-noncompleted-science-state-mismatch",
                "scientific_acceptance",
                f"{status} runs must remain not_assessed",
            )
        )
    for index, evidence in enumerate(data.get("evidence", [])):
        if not isinstance(evidence, dict):
            continue
        evidence_status = evidence.get("status")
        digest = evidence.get("sha256")
        if evidence_status == "present":
            if digest is None:
                findings.append(
                    Finding("run-present-evidence-unhashed", f"evidence/{index}/sha256", "present evidence requires SHA-256")
                )
        elif evidence_status == "missing" and digest is not None:
            findings.append(
                Finding("run-missing-evidence-hashed", f"evidence/{index}/sha256", "missing evidence cannot carry a content hash")
            )
    return findings


def _plan_findings(data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    status = data.get("status")
    blockers = data.get("blockers", [])
    backend = data.get("backend")
    steps = data.get("steps", [])
    missing_required = [
        index
        for index, source in enumerate(data.get("source_files", []))
        if isinstance(source, dict) and source.get("required") is True and source.get("present") is not True
    ]
    if status == "planned":
        if blockers:
            findings.append(Finding("plan-ready-with-blockers", "blockers", "planned execution must have no blockers"))
        if not isinstance(backend, dict) or backend.get("available") is not True:
            findings.append(Finding("plan-backend-unavailable", "backend", "planned execution requires an available backend"))
        elif backend.get("maturity") == "design-only":
            findings.append(Finding("plan-design-only-backend", "backend/maturity", "design-only routes cannot be executed"))
        if not steps:
            findings.append(Finding("plan-ready-without-steps", "steps", "planned execution requires at least one step"))
        for index in missing_required:
            findings.append(
                Finding("plan-required-source-missing", f"source_files/{index}", "required source must be present")
            )
    elif status == "blocked" and not blockers:
        findings.append(Finding("plan-blocked-without-reason", "blockers", "blocked plans require stable blocker evidence"))
    return findings


def _execution_findings(data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    dry_run = data.get("dry_run")
    status = data.get("status")
    return_code = data.get("return_code")
    timing = (data.get("started_utc"), data.get("finished_utc"), data.get("duration_s"))
    if dry_run is True:
        if status != "dry-run":
            findings.append(Finding("execution-dry-run-status-mismatch", "status", "dry-run records must use dry-run status"))
        if any(value is not None for value in timing) or return_code is not None:
            findings.append(Finding("execution-dry-run-runtime-present", "<root>", "dry-run records cannot claim runtime evidence"))
        if data.get("outputs"):
            findings.append(Finding("execution-dry-run-output-present", "outputs", "dry-run records cannot claim produced files"))
    elif status == "dry-run":
        findings.append(Finding("execution-status-dry-run-mismatch", "dry_run", "dry-run status requires dry_run=true"))
    if status == "succeeded":
        if return_code != 0:
            findings.append(Finding("execution-success-return-code", "return_code", "successful execution requires return code zero"))
        if any(value is None for value in timing):
            findings.append(Finding("execution-success-timing-missing", "<root>", "successful execution requires complete timing"))
    if status == "failed" and not data.get("limitations"):
        findings.append(Finding("execution-failure-without-evidence", "limitations", "failed execution requires a failure reason"))
    if status == "timed-out":
        if return_code is not None:
            findings.append(Finding("execution-timeout-return-code", "return_code", "timed-out execution must not invent a return code"))
        if any(value is None for value in timing):
            findings.append(Finding("execution-timeout-timing-missing", "<root>", "timed-out execution requires complete timing"))
    if status == "blocked" and return_code is not None:
        findings.append(Finding("execution-blocked-return-code", "return_code", "blocked execution did not run"))
    return findings


def _dataset_findings(data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    validation = data.get("validation", {})
    validation_status = validation.get("status") if isinstance(validation, dict) else None
    checks = validation.get("checks", []) if isinstance(validation, dict) else []
    if data.get("maturity") == "design-only" and validation_status == "pass":
        findings.append(Finding("dataset-design-only-positive", "maturity", "design-only routes cannot emit a passing dataset"))
    for index, source in enumerate(data.get("source_files", [])):
        if not isinstance(source, dict):
            continue
        if source.get("hash_status") == "present" and source.get("sha256") is None:
            findings.append(
                Finding("dataset-present-source-unhashed", f"source_files/{index}/sha256", "present sources require SHA-256")
            )
    statuses = [check.get("status") for check in checks if isinstance(check, dict)]
    if validation_status == "pass" and any(status != "pass" for status in statuses):
        findings.append(Finding("dataset-pass-check-mismatch", "validation/checks", "passing validation requires every check to pass"))
    if validation_status == "warn" and any(status in {"fail", "not-run"} for status in statuses):
        findings.append(Finding("dataset-warn-check-mismatch", "validation/checks", "warn validation cannot hide failed or unrun checks"))
    if validation_status == "block" and not any(status in {"fail", "not-run"} for status in statuses):
        findings.append(Finding("dataset-block-without-check", "validation/checks", "blocked validation requires failed or unrun evidence"))
    return findings


def _artifact_findings(data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    status = data.get("status")
    validation = data.get("validation", {})
    validation_status = validation.get("status") if isinstance(validation, dict) else None
    if status == "complete":
        if validation_status == "block":
            findings.append(Finding("artifact-complete-validation-blocked", "validation/status", "complete artifacts cannot be blocked"))
        if not data.get("data_files") and not data.get("figure_files"):
            findings.append(Finding("artifact-complete-without-files", "<root>", "complete artifacts require a hashed output"))
        if not data.get("claim_boundary"):
            findings.append(Finding("artifact-complete-without-boundary", "claim_boundary", "complete artifacts require an explicit claim boundary"))
    if validation_status == "block" and status not in {"blocked", "failed", "partial"}:
        findings.append(Finding("artifact-validation-status-mismatch", "status", "blocked validation cannot support completion"))
    return findings


def semantic_findings(kind: str, data: object) -> list[Finding]:
    if kind not in SUPPORTED_KINDS:
        return [Finding("semantic-kind-unsupported", "<root>", f"unsupported semantic kind {kind!r}")]
    schema_errors = validate_contract.validation_errors(kind, data)
    if schema_errors:
        return [Finding("schema-invalid", "<root>", error) for error in schema_errors]
    if not isinstance(data, dict):
        return [Finding("schema-invalid", "<root>", "manifest must be an object")]
    findings = _privacy_findings(data)
    handlers = {
        "run": _run_findings,
        "plan": _plan_findings,
        "execution": _execution_findings,
        "dataset": _dataset_findings,
        "artifact": _artifact_findings,
    }
    findings.extend(handlers[kind](data))
    return sorted(set(findings))


def validate_file(kind: str, path: Path) -> list[Finding]:
    try:
        data = strict_json.load_object(path, path.name)
    except (OSError, strict_json.StrictJSONError) as exc:
        return [Finding("manifest-unreadable", "<file>", str(exc))]
    return semantic_findings(kind, data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=sorted(SUPPORTED_KINDS))
    parser.add_argument("json_file", type=Path)
    args = parser.parse_args()
    findings = validate_file(args.kind, args.json_file)
    if findings:
        for finding in findings:
            print(finding.render(), file=sys.stderr)
        return 2
    print(f"PASS: {args.json_file} is schema-valid, semantically consistent, and privacy-safe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
