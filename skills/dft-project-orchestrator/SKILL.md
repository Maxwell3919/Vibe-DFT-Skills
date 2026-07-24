---
name: dft-project-orchestrator
description: Audit a supplied DFT workflow plan, identify its next evidence-bound action, and check a request against a human decision without executing calculations or scheduler commands. Use for manual coordination across the active CIF, QE, VASP, CP2K, SIESTA, postprocessing, and campaign Skills, especially when the repository route and artifact handoffs must be checked explicitly.
---

# DFT Project Orchestrator

## Start with the repository interface manual

Read [references/repository-interface-manual.md](references/repository-interface-manual.md) before using this candidate. It records the working directory, implemented CLI, real active-Skill entry points, artifact handoffs, route check, runnable synthetic example, and human confirmation points.

## Current status

- **implemented repository interface**: the repository has active contracts for `structure-manifest@1.0`, `run-manifest@1.0`, `artifact-manifest@1.0`, `workflow-plan@1.0`, `decision-record@1.0`, and `execution-request@1.0`, plus active calculation/postprocessing/campaign Skills.
- **implemented candidate-local interface**: `scripts/orchestrator_cli.py` reads supplied JSON and emits an audit JSON document to stdout. It does not emit a production contract.
- **design-only**: this Skill is `development`, source-backed at `skills/dft-project-orchestrator`, and `routable: false`; no registered tool sequence invokes downstream Skills or produces the intended contracts.
- **external not tested**: no DFT executable, scheduler, remote filesystem, credential, or cluster was contacted by the candidate tests.

An active contract does not activate this development Skill. A development-local exit `0` proves only that the bounded local check passed.

## Implemented CLI

Run from the repository root with bytecode disabled:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-project-orchestrator/scripts/orchestrator_cli.py \
  audit-plan \
  --plan skills/dft-project-orchestrator/fixtures/ready-plan.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-project-orchestrator/scripts/orchestrator_cli.py \
  next-action \
  --plan skills/dft-project-orchestrator/fixtures/ready-plan.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-project-orchestrator/scripts/orchestrator_cli.py \
  authorize-check --request REQUEST.json --decision DECISION.json \
  --at-utc 2026-07-19T00:00:00Z
```

The first two commands consume one `workflow-plan` JSON object. `authorize-check` consumes one `execution-request` and one `decision-record`. The tool writes nothing, invokes nothing, and returns one JSON document on stdout.

Exit codes are `0` local check completed/passed, `2` malformed or contract-invalid input, `3` valid input remains blocked, and `4` bounded tool failure. Stop on any nonzero exit. Never read `0` as execution authorization, numerical adequacy, or scientific acceptance.

Every command is a dry-run inspection: require `dry_run=true`, `side_effect_performed=false`, `lease_issued=false`, and `workflow_event_emitted=false` in its report. Build any final structured response as `agent-action-envelope@1.0` and validate it with `tools/validate_agent_answer.py`; the candidate report is evidence input, not the answer contract.

## Manual workflow

1. Check the requested Skill with `tools/operation_routes.py route <skill-id>`. Stop if the route tool is nonzero or the route is non-active, blocked, or null.
2. Validate every active contract artifact with `tools/validate_contract.py`; validate a content-addressed bundle with `tools/validate_bundle.py` when a bundle manifest exists.
3. Audit the supplied workflow plan and ask `next-action` for one bounded next step.
4. Obtain human confirmation before selecting an engine, changing scientific choices, authorizing execution, cancelling work, or accepting a scientific claim.
5. Invoke the chosen active Skill manually. This candidate never calls QE, VASP, CP2K, or SIESTA.
6. After a terminal calculation event, create `run-manifest@1.0`, then hand it manually to `$dft-postprocess` and `$dft-campaign-efficiency` using the exact commands in the manual.
7. Persist artifacts and hashes outside conversation memory; rerun route and contract checks at every handoff.

## Failure and authority rules

- Missing, stale, mismatched, or unresolvable hashes block the handoff.
- A process exit code, scheduler state, application completion marker, numerical convergence assessment, and human scientific decision are separate facts.
- The candidate cannot create a valid human decision, execution lease, scheduler job, scientific acceptance, or publication decision.
- Do not invent site policy, software version, pseudopotential/basis provenance, observables, tolerances, or resource limits.
- A downstream active Skill's own deterministic gate and human-review boundary remain authoritative.

## Additional references

- Use [references/practical-playbooks.md](references/practical-playbooks.md) for new-campaign, convergence, restart, failure-triage, and publication-evidence workflows.
- Use [references/fail-closed-contract.md](references/fail-closed-contract.md) and [references/decision-table.md](references/decision-table.md) for candidate-local gate order.
- Use [references/weak-model-decision-table.json](references/weak-model-decision-table.json) for deterministic first-match response routing.
- Use [references/finding-catalog.json](references/finding-catalog.json) for stable finding meanings.
- Use [references/maturity-matrix.json](references/maturity-matrix.json) before any promotion discussion.
- Use [references/source-pack-seed.json](references/source-pack-seed.json) and [references/source-pack-scope-catalog.json](references/source-pack-scope-catalog.json) for the blocked metadata-only repository/JSON-Schema source boundary; refresh or check them with `scripts/extract_official_source_scope.py`.

The maximum claim while this Skill is development/non-routable is `no_positive_claim`.
