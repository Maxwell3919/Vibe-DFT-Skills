---
name: ovito-atomistic-analysis
description: Inventory XYZ or extended-XYZ trajectories, validate version- and edition-bound OVITO analysis or rendering pipeline plans, probe provider metadata, and execute only an explicitly authorized pinned frame-metadata route with traceable JSON evidence. Use when atomistic trajectories need periodicity, frame, property, atom-order, selector, analysis, rendering, or license gates without confusing parser output, a planned pipeline, a visual artifact, and an actual OVITO result. This is an isolated development Skill and must not be routed as an active production skill.
---

# OVITO Atomistic Analysis

Read [the local official-manual cache route](references/manual-cache-route.md) before relying on external OVITO documentation or package metadata.

## Hold the authority boundary

Treat this directory as non-routable candidate evidence. Never call it installed, active,
scientifically validated, or generally OVITO-compatible. Keep these states distinct:

- `parser-only`: the standard-library XYZ/extxyz inventory ran; OVITO did not.
- `planned-not-executed`: a pipeline specification passed shape and policy gates; OVITO did not.
- `distribution-metadata-only`: package metadata was inspected; no import or pipeline ran.
- `actual-external-execution`: an authorized, exact-version OVITO module computed the one
  candidate-implemented frame-metadata route.

Separate router, deterministic planner, external executor, evidence reviewer, and scientific
decision roles. Never let a plan, probe, screenshot, or synthetic API double impersonate another
role's evidence.

## Route the request

Choose exactly one primary route:

- Use `inventory` to parse and hash XYZ/extxyz frames without importing OVITO.
- Use `plan` to validate source identity, edition/version, frame selection, mapping/PBC policy,
  operation parameters, evidence role, and output labels without importing OVITO.
- Use `probe` to inspect distribution metadata without importing the module.
- Use `execute` only for `compute-frame-metadata`, after explicit user authorization.
- Refuse to execute coordination, CNA, strain, dislocation, export, or rendering routes; they are
  plan-only in this candidate.

Read [analysis-recipes.md](references/analysis-recipes.md) for official 3.15.5 import/mapping,
pipeline order, selections, CNA/PTM/DXA/Wigner-Seitz/displacement/strain/RDF, averaging, rendering,
export, and validation behavior. It separates provider facts from operational heuristics. Read
[pipeline-workflow.md](references/pipeline-workflow.md) before planning. Read
[fail-closed-contract.md](references/fail-closed-contract.md) before any external execution. Read
[official-sources-and-environment.md](references/official-sources-and-environment.md) before
selecting Basic or Pro. For mechanical routing, parse the machine-readable
[decision table](references/weak-model-decision-table.json) and never take an action stronger than
its `minimum_next_action`.

## Execute the low-reasoning workflow

1. Inventory the exact immutable trajectory:

   ```bash
   python3 scripts/ovito_analysis.py inventory TRAJECTORY.extxyz --out INVENTORY.json
   ```

2. Inspect `status`, source SHA-256, frame count, atom-count continuity, species-order continuity,
   `particle_identifier_status`, property-schema continuity, PBC/cell mode, source-native length
   unit state, available fields, mapping state, findings,
   `ovito_executed=false`, and the candidate lifecycle fields.
3. Create a candidate pipeline matching
   [the local pipeline schema](schemas/ovito-pipeline-spec-candidate.schema.json). Bind it to the
   inventory's exact source hash and format. Use basenames, never output paths.
4. Validate the plan without OVITO:

   ```bash
   python3 scripts/ovito_analysis.py plan --inventory INVENTORY.json --pipeline PIPELINE.json --out PLAN.json
   ```

5. Inspect `execution_readiness`, every operation's `candidate_execution`, provider edition,
   findings, `execution_state=planned-not-executed`, and `authorization_scope_sha256`. Add
   `--require-execution-ready` at an execution boundary.
6. Probe only when exact provider identity matters:

   ```bash
   python3 scripts/ovito_analysis.py probe
   ```

7. Execute only after the user explicitly authorizes local external execution, only with the
   `ovito` Python distribution at exact version `3.15.5` (the candidate's internal
   `ovito-basic` profile), and only when every operation is `compute-frame-metadata`:

   ```bash
   python3 scripts/ovito_analysis.py execute --source TRAJECTORY.extxyz \
     --inventory INVENTORY.json --pipeline PIPELINE.json --authorize-execution \
     --authorization-scope PLAN_SCOPE_SHA256 --out RESULT.json
   ```

8. Verify the result says `actual-external-execution`, `ovito_executed=true`, the exact imported
   version, the bound source hash, selected frames, executed operation list, `sort_particles=false`
   order policy, cell vectors, particle identifiers when inventoried, and limitations.

## Apply the non-negotiable gates

- Refuse symlink, changing, non-regular, oversized, non-UTF-8, malformed, truncated, non-finite,
  or duplicate-key input.
- Require declared atom counts to match every frame and preserve exact source bytes and SHA-256.
- Validate every declared extxyz property type and count. Treat changed atom count, species order,
  property schema, PBC, or cell presence as unresolved cross-frame analysis state.
- Treat XYZ order as ordinal-only unless every frame carries the same unique scalar integer
  `id:I:1` set. Reordering is then traceable by identifier, but a species/identifier mismatch blocks.
- Treat XYZ/extxyz coordinates as source-native and unit-unaware. Require an explicit
  `source_length_unit` before accepting any numerical cutoff.
- Require periodic frames to have a finite nonsingular `Lattice`; do not infer missing PBC.
- Bind pipeline source hash and format to the inventory; refuse out-of-range or duplicate frames.
- Require exact parameter keys and operation-specific evidence roles.
- Keep standalone-module availability, Basic desktop features, and Pro desktop entitlement
  separate. Do not infer a Pro entitlement from installation, package metadata, or a user account.
- Refuse every plan-only operation at execution, even if an OVITO module happens to provide it.
- Refuse unpinned/mismatched distribution or imported versions, missing or mismatched bound
  authorization scope, source hash drift, existing/evidence-alias output, and symlinked output
  parents.

## Interpret evidence conservatively

An inventory proves only the candidate parser's observations. A plan proves only specification
and policy checks. A probe proves only distribution metadata. An authorized execution proves only
the emitted technical frame metadata for the exact source, frames, provider, and operation.

Images and animations are visual artifacts, not numerical validation. Visual inspection may
detect obvious discontinuities or rendering problems but cannot establish coordination counts,
defect populations, strain, dislocation topology, convergence, or physical correctness. Read
[visual-and-numerical-boundaries.md](references/visual-and-numerical-boundaries.md).

While this directory is in development and non-routable, every current report remains
`claim_ceiling=no_positive_claim`, `promotion_authorized=false`, and
`execution_authorized=false`. `future_gate_ceiling=technical_run_gates_only` on an actual bounded
metadata run describes only a potential post-promotion ceiling. Explicit CLI authorization is
recorded separately and never promotes the candidate or accepts a scientific claim.

## Respect maturity and activation limits

Consult [task-profiles-and-maturity.md](references/task-profiles-and-maturity.md) per operation,
edition, version, and parent route. Consult [finding-catalog.md](references/finding-catalog.md)
before changing failure handling. The synthetic API double in unit tests validates invocation
shape only and is not OVITO integration evidence.

This candidate emits local `0.1` schemas, not the planned shared `ovito-pipeline-spec@1.0`.
Read [data-contracts.md](references/data-contracts.md) before shared-contract adaptation.

## Validate this candidate

Run the isolated unit suite, skill validator, and candidate validation at L0 and L1. Verify hashes
against [fixture-manifest.json](references/fixture-manifest.json) and inspect
[validation-state.json](references/validation-state.json) for the latest machine-readable local
result and unresolved repository gates. Activation additionally needs
licensed real artifacts, a commit-aware shared pipeline contract, exact Basic integration tests,
separately authorized Pro tests, numerical reference comparisons, rendering provenance and visual
QA, expert review, and registry promotion. Local candidate passes cannot satisfy those conditions.
