#!/usr/bin/env python3
"""Render a deterministic Phase A1 readiness projection from canonical registries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Sequence

sys.dont_write_bytecode = True

from registry_snapshot import RegistrySnapshotError, load_registry_snapshot


SCHEMA_VERSION = "1.0"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _report(root: Path) -> dict[str, Any]:
    snapshot = load_registry_snapshot(root, validate_sources=True)
    evidence_records = snapshot.active_evidence["records"]
    routes = snapshot.operation_routes["routes"]
    policy = snapshot.operation_routes["response_policy"]
    terminal_targets = policy["terminal_intent_routes"]
    terminal_requirements = policy["terminal_intent_requirements"]
    terminal_reasons = policy["terminal_intent_blocked_reasons"]

    active_skills = []
    prohibited_claims: set[str] = set()
    legacy_skill_ids: list[str] = []
    verified_skill_ids: list[str] = []
    for skill_id, skill in sorted(snapshot.skills["skills"].items()):
        if skill["lifecycle"] != "active":
            continue
        evidence = evidence_records[skill_id]
        route = routes[skill_id]
        status = evidence["activation_evidence_status"]
        if status == "legacy-unclosed":
            legacy_skill_ids.append(skill_id)
        elif status == "verified":
            verified_skill_ids.append(skill_id)
        prohibited_claims.update(evidence["prohibited_claims"])
        active_skills.append(
            {
                "skill_id": skill_id,
                "lifecycle": skill["lifecycle"],
                "source_tree_sha256": skill["source_tree_sha256"],
                "activation_evidence_status": status,
                "route_maturity_refs": evidence["route_maturity_refs"],
                "routable_actions": sorted(route["actions"]),
            }
        )

    terminal_intents = [
        {
            "intent": intent,
            "target": target,
            "readiness_class": terminal_requirements[intent][
                "readiness_class"
            ],
            "requirement": terminal_requirements[intent],
            "reason": terminal_reasons.get(intent),
        }
        for intent, target in sorted(terminal_targets.items())
    ]
    missing_route_intents = [
        item
        for item in terminal_intents
        if item["readiness_class"] == "missing-route"
        and item["target"] is None
    ]
    ready_route_intents = [
        item["intent"]
        for item in terminal_intents
        if item["readiness_class"] == "missing-route"
        and item["target"] is not None
    ]
    human_boundary_intents = [
        item["intent"]
        for item in terminal_intents
        if item["readiness_class"] == "human-boundary"
    ]
    intentionally_disabled_intents = [
        item["intent"]
        for item in terminal_intents
        if item["readiness_class"] == "intentionally-disabled"
    ]
    automatable_intent_count = len(missing_route_intents) + len(
        ready_route_intents
    )
    automated_intent_count = len(ready_route_intents)
    coverage_ratio = (
        automated_intent_count / automatable_intent_count
        if automatable_intent_count
        else 1.0
    )
    automation_status = (
        "full"
        if automated_intent_count == automatable_intent_count
        else "none"
        if automated_intent_count == 0
        else "partial"
    )
    activation_status = "not-ready" if legacy_skill_ids else "ready"
    operational_status = "not-ready" if missing_route_intents else "ready"
    finding_codes = []
    if legacy_skill_ids:
        finding_codes.append("ACTIVE_EVIDENCE_LEGACY_UNCLOSED")
    if missing_route_intents:
        finding_codes.append("OPERATIONAL_ROUTE_MISSING")
    aggregate_readiness = (
        "ready"
        if activation_status == "ready" and operational_status == "ready"
        else "not-ready"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "report_id": "vibedft-phase-a1-readiness",
        "aggregate_readiness": aggregate_readiness,
        "aggregate_readiness_basis": [
            "activation_evidence_readiness",
            "operational_readiness",
        ],
        "activation_evidence_readiness": {
            "status": activation_status,
            "active_skill_count": len(active_skills),
            "verified_count": len(verified_skill_ids),
            "verified_skill_ids": verified_skill_ids,
            "legacy_unclosed_count": len(legacy_skill_ids),
            "legacy_unclosed_skill_ids": legacy_skill_ids,
        },
        "operational_readiness": {
            "status": operational_status,
            "missing_route_intents": missing_route_intents,
            "ready_route_intents": ready_route_intents,
        },
        "automation_coverage": {
            "status": automation_status,
            "automatable_intent_count": automatable_intent_count,
            "automated_intent_count": automated_intent_count,
            "coverage_ratio": coverage_ratio,
            "human_boundary_intents": human_boundary_intents,
            "intentionally_disabled_intents": intentionally_disabled_intents,
        },
        "active_skills": active_skills,
        "terminal_intents": terminal_intents,
        "claim_readiness_limitations": sorted(prohibited_claims),
        "finding_codes": sorted(finding_codes),
    }


def render_report(root: Path | None = None) -> str:
    """Return canonical JSON bytes as text after validating the full snapshot."""

    return json.dumps(
        _report((root or repo_root()).resolve()),
        indent=2,
        sort_keys=True,
    ) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root())
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate and render without changing the blocked/ready exit status.",
    )
    args = parser.parse_args(argv)
    try:
        report = render_report(args.root)
    except (OSError, UnicodeError, ValueError, RegistrySnapshotError) as exc:
        print(
            f"VIBEDFT_READINESS_INVALID: {exc.__class__.__name__}: {exc}",
            file=sys.stderr,
        )
        return 2
    if not args.check:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
