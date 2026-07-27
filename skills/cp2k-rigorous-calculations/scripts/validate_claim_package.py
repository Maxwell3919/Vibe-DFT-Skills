#!/usr/bin/env python3
"""Validate a CP2K evidence package; trust cached bytes or an explicit in-process live replay."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

import audit_cp2k_case
import resolve_official_sources


SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROFILES = SKILL_ROOT / "references" / "task-evidence-profiles.json"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
CP2K_RELEASE = re.compile(r"\bCP2K version\s+([0-9]+\.[0-9]+(?:\.[0-9]+)?)\b", re.IGNORECASE)
PACKAGE_KEYS = {
    "schema_version",
    "claim_id",
    "task_type",
    "observable",
    "unit",
    "absolute_tolerance",
    "relative_tolerance",
    "audit_json",
    "convergence_json",
    "official_sources_json",
    "checks",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is invalid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return value


def resolved_path(value: Any, base: Path, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty path")
    path = Path(value)
    return path if path.is_absolute() else base / path


def finite_nonnegative(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{label} must be finite and non-negative")
    return result


def load_task_profile(task_type: str, profiles_path: Path = DEFAULT_PROFILES) -> tuple[bool, set[str]]:
    document = load_object(profiles_path, "task evidence profiles")
    if document.get("schema_version") != "1.1":
        raise ValueError("unsupported task evidence profile schema")
    profile = document.get("profiles", {}).get(task_type)
    common = document.get("common_claim_checks")
    if not isinstance(profile, dict):
        raise ValueError(f"unsupported task_type: {task_type}")
    specific = profile.get("required_claim_checks")
    if not isinstance(common, list) or not isinstance(specific, list):
        raise ValueError("task evidence profile has invalid claim checks")
    return bool(profile.get("claim_supported")), {str(value) for value in common + specific}


def load_passing_audit(path: Path) -> dict[str, Any]:
    audit = load_object(path, "audit evidence")
    if audit.get("audit_schema_version") != "1.0" or audit.get("auditor") != "audit_cp2k_case.py":
        raise ValueError("audit evidence has an unexpected schema or producer")
    if audit.get("mode") != "run" or audit.get("decision") != "pass":
        raise ValueError("audit evidence is not a passing CP2K run audit")
    if audit.get("verdict") != "technical_run_gates_passed_scientific_claim_blocked":
        raise ValueError("audit evidence has an unexpected verdict")
    gates = audit.get("gates")
    required = {
        "input_integrity": {"pass"},
        "input_reproducibility": {"pass"},
        "task_profile": {"pass"},
        "method_profile": {"pass"},
        "evidence_inventory": {"pass"},
        "execution_completion": {"pass"},
        "electronic_convergence": {"pass"},
        "ionic_or_task_completion": {"pass", "not_applicable"},
        "output_warnings": {"pass"},
        "version_identity": {"pass"},
        "input_output_binding": {"pass"},
        "runtime_environment": {"pass"},
        "numerical_convergence": {"not_evaluated_by_single_case"},
        "physical_validity": {"not_evaluated_by_single_case"},
        "scientific_claim": {"blocked"},
    }
    if not isinstance(gates, dict) or any(gates.get(name) not in allowed for name, allowed in required.items()):
        raise ValueError("audit evidence has an incomplete or blocked gate map")
    summary = audit.get("summary")
    output = audit.get("files", {}).get("output")
    profiles = audit.get("profiles")
    if not isinstance(summary, dict) or summary.get("errors") != 0:
        raise ValueError("audit evidence contains errors")
    if not isinstance(output, dict) or not isinstance(output.get("version"), str):
        raise ValueError("audit evidence has no CP2K version identity")
    version_match = CP2K_RELEASE.search(output["version"])
    if version_match is None:
        raise ValueError("audit CP2K release cannot be normalized")
    if not isinstance(profiles, dict) or not isinstance(profiles.get("task"), dict) or not isinstance(profiles.get("methods"), list):
        raise ValueError("audit evidence has no task/method profiles")
    task_type = audit.get("task_type")
    if not isinstance(task_type, str) or task_type not in audit_cp2k_case.TASK_PROFILES:
        raise ValueError("audit evidence has an unsupported task profile")
    expected_base_topics = set(audit_cp2k_case.QUICKSTEP_BASE_SOURCE_TOPICS)
    expected_task_only = set(audit_cp2k_case.TASK_PROFILES[task_type]["required_source_topics"])
    expected_task_topics = set(audit_cp2k_case.task_source_topics(task_type))
    task_profile = profiles["task"]
    actual_base_topics = set(
        audit_cp2k_case.source_topic_list(
            task_profile.get("quickstep_base_source_topics"),
            "audit quickstep_base_source_topics",
        )
    )
    actual_task_only = set(
        audit_cp2k_case.source_topic_list(
            task_profile.get("task_source_topics"),
            "audit task_source_topics",
        )
    )
    actual_task_topics = set(
        audit_cp2k_case.source_topic_list(
            task_profile.get("required_source_topics"),
            "audit required_source_topics",
        )
    )
    if (
        task_profile.get("name") != task_type
        or actual_base_topics != expected_base_topics
        or actual_task_only != expected_task_only
        or actual_task_topics != expected_task_topics
    ):
        raise ValueError("audit task profile does not inherit the checked-in Quickstep source topics")
    required_topics = set(expected_task_topics)
    detected_methods: set[str] = set()
    for method in profiles["methods"]:
        if not isinstance(method, dict) or not isinstance(method.get("name"), str):
            raise ValueError("audit method profile is malformed")
        name = method["name"]
        expected_method = audit_cp2k_case.METHOD_PROFILES.get(name)
        if (
            expected_method is None
            or name in detected_methods
            or set(
                audit_cp2k_case.source_topic_list(
                    method.get("source_topics"),
                    f"audit {name}.source_topics",
                )
            )
            != set(expected_method["source_topics"])
        ):
            raise ValueError("audit method profile differs from the checked-in source requirements")
        detected_methods.add(name)
        required_topics.update(expected_method["source_topics"])
    if "quickstep-core" not in detected_methods:
        raise ValueError("audit method profile omits the Quickstep core")
    if not required_topics or any(not isinstance(value, str) for value in required_topics):
        raise ValueError("audit official-source requirements are unresolved")
    return {
        "sha256": sha256_file(path),
        "case_id": audit.get("case_id"),
        "task_type": audit.get("task_type"),
        "cp2k_version": version_match.group(1),
        "required_source_topics": required_topics,
    }


def validate_official_sources(
    path: Path,
    version: str,
    required_topics: set[str],
    *,
    live_replay: bool = False,
    snapshot_dir: Path = resolve_official_sources.DEFAULT_SNAPSHOT,
) -> dict[str, Any]:
    evidence = load_object(path, "official-source evidence")
    if (
        evidence.get("schema_version") != "1.1"
        or evidence.get("manual_version") != version
        or evidence.get("manual_branch") != resolve_official_sources.manual_branch(version)
    ):
        raise ValueError("official-source evidence version differs from the audited CP2K release")
    if evidence.get("status") == "pass_live_matches_cached":
        raise ValueError(
            "self-declared live receipt is not a trust root; submit cached_exact evidence and request live replay"
        )
    if evidence.get("status") != "pass_cached_exact":
        raise ValueError("official-source evidence is not version-verified")
    resolved = evidence.get("resolved")
    if not isinstance(resolved, list):
        raise ValueError("official-source evidence has no resolved records")
    by_topic: dict[str, dict[str, Any]] = {}
    for record in resolved:
        if not isinstance(record, dict) or not isinstance(record.get("topic"), str):
            raise ValueError("official-source evidence contains a malformed record")
        if record["topic"] in by_topic:
            raise ValueError("official-source evidence contains a duplicate topic")
        if record.get("verification") != "cached_exact":
            raise ValueError("official-source evidence contains an unverified topic")
        by_topic[record["topic"]] = record
    missing = sorted(required_topics - set(by_topic))
    if missing:
        raise ValueError(f"official-source evidence is missing {len(missing)} required topic(s)")
    unexpected = sorted(set(by_topic) - required_topics)
    if unexpected:
        raise ValueError(f"official-source evidence contains {len(unexpected)} unexpected topic(s)")
    if {record["verification"] for record in by_topic.values()} != {"cached_exact"}:
        raise ValueError("official-source evidence mixes incompatible verification states")
    if evidence["status"] != "pass_cached_exact":
        raise ValueError("official-source evidence status differs from its verification records")

    cached = resolve_official_sources.resolve(
        sorted(required_topics),
        version,
        live_check=False,
        snapshot_dir=snapshot_dir,
    )
    if cached.get("status") != "pass_cached_exact":
        raise ValueError(
            "the configured official provider snapshot cannot independently verify every required topic"
        )
    expected = {record["topic"]: record for record in cached["resolved"]}
    for topic in required_topics:
        record = by_topic[topic]
        reference = expected[topic]
        if record.get("url") != reference.get("url"):
            raise ValueError("official-source URL differs from the checked-in registry")
        if (
            record.get("snapshot_sha256") != reference.get("snapshot_sha256")
            or record.get("source_content_sha256") != reference.get("source_content_sha256")
            or record.get("snapshot_bytes") != reference.get("snapshot_bytes")
            or record.get("source_content_bytes") != reference.get("source_content_bytes")
            or record.get("local_reference") != reference.get("local_reference")
            or record.get("cached_retrieved_utc") != reference.get("cached_retrieved_utc")
        ):
            raise ValueError("official-source snapshot hashes do not match the checked-in manifest")
    verification_mode = "cached_exact"
    if live_replay:
        replay = resolve_official_sources.resolve(
            sorted(required_topics),
            version,
            live_check=True,
            snapshot_dir=snapshot_dir,
        )
        if replay.get("status") != "pass_live_matches_cached":
            raise ValueError(
                "validation-time live replay did not match the configured official provider snapshot"
            )
        verification_mode = "live_replayed_matches_cached"
    return {
        "sha256": sha256_file(path),
        "manual_version": version,
        "required_topics": sorted(required_topics),
        "verified_topics": len(required_topics),
        "verification_mode": verification_mode,
    }


def validate_checks(value: Any, required: set[str], base: Path) -> dict[str, Any]:
    if not isinstance(value, list):
        raise ValueError("checks must be an array")
    records: dict[str, dict[str, Any]] = {}
    malformed: list[str] = []
    for index, source_record in enumerate(value):
        if not isinstance(source_record, dict):
            malformed.append(f"checks[{index}] is not an object")
            continue
        check_id = source_record.get("id")
        if not isinstance(check_id, str) or not SAFE_ID.fullmatch(check_id):
            malformed.append(f"checks[{index}] has an invalid id")
            continue
        if check_id in records:
            malformed.append(f"duplicate check id: {check_id}")
            continue
        evidence_files = source_record.get("evidence_files")
        hashes: list[str] = []
        if not isinstance(evidence_files, list) or not evidence_files or any(
            not isinstance(item, str) or not item.strip() for item in evidence_files
        ):
            malformed.append(f"{check_id} requires one or more evidence files")
        else:
            for item in evidence_files:
                evidence_path = Path(item)
                if not evidence_path.is_absolute():
                    evidence_path = base / evidence_path
                if not evidence_path.is_file():
                    malformed.append(f"{check_id} evidence file is missing")
                    continue
                hashes.append(sha256_file(evidence_path))
        record = dict(source_record)
        record["computed_evidence_sha256"] = hashes
        records[check_id] = record
    missing = sorted(required - set(records))
    unexpected = sorted(set(records) - required)
    blocked = sorted(check_id for check_id in required & set(records) if records[check_id].get("status") != "pass")
    status = "pass" if not (malformed or missing or unexpected or blocked) else "blocked"
    return {
        "status": status,
        "required": sorted(required),
        "missing": missing,
        "unexpected": unexpected,
        "blocked": blocked,
        "malformed": malformed,
        "evidence": {
            check_id: sorted(set(records[check_id].get("computed_evidence_sha256", [])))
            for check_id in sorted(required & set(records))
        },
    }


def validate_package(
    package_path: Path,
    profiles_path: Path = DEFAULT_PROFILES,
    *,
    live_replay: bool = False,
    snapshot_dir: Path = resolve_official_sources.DEFAULT_SNAPSHOT,
) -> dict[str, Any]:
    package = load_object(package_path, "claim package")
    missing_keys = sorted(PACKAGE_KEYS - set(package))
    extra_keys = sorted(set(package) - PACKAGE_KEYS)
    if missing_keys or extra_keys:
        raise ValueError(f"claim package keys invalid; missing={missing_keys}, extra={extra_keys}")
    if package.get("schema_version") != "1.0":
        raise ValueError("unsupported claim package schema")
    claim_id = package.get("claim_id")
    task_type = package.get("task_type")
    if not isinstance(claim_id, str) or not SAFE_ID.fullmatch(claim_id):
        raise ValueError("claim_id must be an opaque safe identifier")
    if not isinstance(task_type, str):
        raise ValueError("task_type must be a string")
    claim_supported, required_checks = load_task_profile(task_type, profiles_path)
    observable = package.get("observable")
    unit = package.get("unit")
    if not isinstance(observable, str) or not observable.strip() or not isinstance(unit, str) or not unit.strip():
        raise ValueError("observable and unit must be nonempty strings")
    abs_tol = finite_nonnegative(package.get("absolute_tolerance"), "absolute_tolerance")
    rel_tol = finite_nonnegative(package.get("relative_tolerance"), "relative_tolerance")

    base = package_path.parent
    audit_path = resolved_path(package.get("audit_json"), base, "audit_json")
    convergence_path = resolved_path(package.get("convergence_json"), base, "convergence_json")
    official_path = resolved_path(package.get("official_sources_json"), base, "official_sources_json")
    audit = load_passing_audit(audit_path)
    convergence = load_object(convergence_path, "convergence evidence")
    official = validate_official_sources(
        official_path,
        audit["cp2k_version"],
        audit["required_source_topics"],
        live_replay=live_replay,
        snapshot_dir=snapshot_dir,
    )
    blockers: list[str] = []
    if not claim_supported:
        blockers.append("generic task profile cannot support a claim package")
    if audit["task_type"] != task_type:
        blockers.append("audit task_type differs from claim package")
    if convergence.get("convergence_schema_version") != "1.0" or convergence.get("analyzer") != "analyze_convergence.py":
        blockers.append("convergence evidence has an unexpected schema or producer")
    if convergence.get("status") != "candidate_found":
        blockers.append("convergence evidence has no stable-tail candidate")
    if convergence.get("task_type") != task_type:
        blockers.append("convergence task_type differs from claim package")
    if convergence.get("observable") != observable or convergence.get("unit") != unit:
        blockers.append("convergence observable or unit differs from claim package")
    criterion = convergence.get("criterion")
    if not isinstance(criterion, dict) or criterion.get("absolute_tolerance") != abs_tol or criterion.get("relative_tolerance") != rel_tol:
        blockers.append("convergence tolerance differs from claim package")
    series = convergence.get("series")
    audit_hashes = {
        item.get("audit_sha256")
        for item in series
        if isinstance(item, dict) and isinstance(item.get("audit_sha256"), str)
    } if isinstance(series, list) else set()
    if audit["sha256"] not in audit_hashes:
        blockers.append("selected run audit is not part of the convergence series")
    expected_gates = {
        "technical_run_evidence": "pass",
        "declared_protocol_consistency": "pass",
        "declared_comparability": "pass",
        "declared_state_continuity": "pass",
        "numerical_stable_tail": "pass",
        "physical_validity": "not_assessed",
    }
    convergence_gates = convergence.get("gates")
    if not isinstance(convergence_gates, dict) or any(convergence_gates.get(name) != status for name, status in expected_gates.items()):
        blockers.append("convergence gate map is incomplete or blocked")
    checks = validate_checks(package.get("checks"), required_checks, base)
    if checks["status"] != "pass":
        blockers.append("task evidence checks are incomplete or blocked")
    eligible = not blockers
    return {
        "claim_package_schema_version": "1.0",
        "claim_id": claim_id,
        "task_type": task_type,
        "case_id": audit["case_id"],
        "observable": observable,
        "unit": unit,
        "audit_sha256": audit["sha256"],
        "convergence_sha256": sha256_file(convergence_path),
        "official_sources_sha256": official["sha256"],
        "official_sources": {
            "manual_version": official["manual_version"],
            "required_topics": official["required_topics"],
            "verified_topics": official["verified_topics"],
            "verification_mode": official["verification_mode"],
        },
        "checks": checks,
        "blockers": blockers,
        "gates": {
            "technical_run_evidence": "pass",
            "version_matched_official_sources": "pass",
            "numerical_convergence_candidate": "pass" if convergence.get("status") == "candidate_found" else "fail",
            "task_specific_evidence_package": checks["status"],
            "physical_validity": "declared_evidence_complete_not_independently_verified" if eligible else "unresolved",
            "scientific_acceptance": "requires_expert_review" if eligible else "blocked",
        },
        "status": "eligible_for_expert_review" if eligible else "blocked",
        "maximum_allowed_conclusion": (
            "The structured CP2K evidence package is complete for expert scientific review; it is not automatically accepted."
            if eligible
            else "No scientific claim is allowed until every blocker is resolved."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--profiles", type=Path, default=DEFAULT_PROFILES)
    parser.add_argument(
        "--live-replay",
        action="store_true",
        help="Reopen every required official URL during this validation and require exact cached-content hashes.",
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=resolve_official_sources.DEFAULT_SNAPSHOT,
        help="Provider snapshot directory used to independently verify official-source evidence.",
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_package(
            args.package,
            args.profiles,
            live_replay=args.live_replay,
            snapshot_dir=args.snapshot,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "blocked_invalid_package", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result["status"] == "eligible_for_expert_review" else 2


if __name__ == "__main__":
    raise SystemExit(main())
