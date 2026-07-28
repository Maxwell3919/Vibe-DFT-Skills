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
    terminal_reasons = policy["terminal_intent_blocked_reasons"]

    active_skills = []
    prohibited_claims: set[str] = set()
    legacy_present = False
    for skill_id, skill in sorted(snapshot.skills["skills"].items()):
        if skill["lifecycle"] != "active":
            continue
        evidence = evidence_records[skill_id]
        route = routes[skill_id]
        status = evidence["activation_evidence_status"]
        legacy_present = legacy_present or status == "legacy-unclosed"
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

    blocked_terminal_intents = [
        {
            "intent": intent,
            "reason": terminal_reasons[intent],
        }
        for intent, target in sorted(terminal_targets.items())
        if target is None
    ]
    finding_codes = []
    if legacy_present:
        finding_codes.append("ACTIVE_EVIDENCE_LEGACY_UNCLOSED")
    if blocked_terminal_intents:
        finding_codes.append("TERMINAL_INTENT_BLOCKED")
    aggregate_readiness = (
        "blocked"
        if finding_codes
        else "ready"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "report_id": "vibedft-phase-a1-readiness",
        "aggregate_readiness": aggregate_readiness,
        "active_skills": active_skills,
        "blocked_terminal_intents": blocked_terminal_intents,
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
