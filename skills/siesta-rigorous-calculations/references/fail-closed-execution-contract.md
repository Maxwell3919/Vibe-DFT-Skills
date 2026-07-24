# SIESTA fail-closed execution contract

## Gate order

Evaluate in order; later observations never repair an earlier failed gate.

1. `scientific_plan` — immutable case/protocol/state, version, task, observable, units, normalization/reference, tolerance, and acceptance criteria are valid.
2. `official_source_resolution` — decisive FDF labels and behaviors are covered by the pinned version/commit evidence set.
3. `fdf_syntax` — direct input can be represented without includes, redirection, duplicate canonical labels, or malformed blocks.
4. `fdf_semantics` — every official label is also in the automated task-profile allowlist.
5. `structure_consistency` — atom/species counts, coordinate species, cell, and periodic sampling agree.
6. `pseudopotential_provenance` — exact local file identities and required scientific metadata match schema 2.0.
7. `numerical_controls` — basis, mesh, XC, SCF, sampling, state, and task controls required by the profile are explicit.
8. `parent_ancestry` — downstream/restart parents match code/version/case/protocol and provide hashed evidence roles.
9. `official_version_match` — the unique output version equals the plan, expected executable, and pinned evidence version.
10. `input_output_consistency` — the unique normalized output input-dump equals the audited direct FDF.
11. `execution_completion` — exactly one start/end/completion boundary exists and fatal markers are absent.
12. `electronic_convergence` — SCF convergence is observed and `SCF_NOT_CONV` is absent.
13. `output_warnings` — no unresolved SIESTA warning marker exists.
14. `output_observables` — profile-required and scientific-plan observables are extracted from the terminal output blocks.
15. `numerical_convergence` — distinct rehashed artifacts support a named observable/tolerance stable tail.
16. `task_specific_validity` — task prerequisites and consistency tests pass; only fixed-cell relaxation has an automated core.
17. `physical_validity` — independent physical/model checks pass.
18. `scientific_acceptance` — every gate required by the declared claim passes.

The auditor automates 1–14 for its SCF/direct-FDF surface and 16 for fixed-cell relaxation. Input mode marks run-only gates not applicable. A single audit leaves 15 and 17 not assessed and 18 blocked. The convergence analyzer can support 15 only; it does not upgrade 16–18.

SIESTA 5.4.2 writes a separate effective `fdf.*.log` containing defaults but exposes no CLI switch that embeds the direct input in standard output. A run wrapper must therefore prepend the exact direct FDF between the auditor's unique input-dump markers before appending SIESTA stdout. Do not substitute the expanded effective-FDF log for direct-input equality.

## Failure precedence

- Any error finding blocks the whole audit, even if it belongs to a gate outside the normal positive core.
- `SCF_NOT_CONV` and `GEOM_NOT_CONV` override `Job completed`.
- Warnings are unresolved evidence and block a zero-warning technical pass.
- More than one version/start/end/completion marker is concatenated or ambiguous output and blocks.
- An output value is admissible only when the output hash and input echo match the audit evidence.
- An offline resolver result is `cached_only` (exit 3), not a live-source pass.

## Safety and privacy

- Default to read-only inspection; require authorization for execution, scheduling, restart, overwrite, deletion, or installation.
- Resolve scripts from the skill directory, not the calculation directory.
- Emit opaque identifiers, hashes, selected non-sensitive fields, finding codes, gate states, and extracted terminal metrics.
- Emit no absolute runtime paths, raw pseudopotential content, source identity strings, or unpublished structure/output excerpts.
- Treat nonzero tool exits as blocking. Do not edit generated JSON to obtain a pass.

## Maximum conclusions

- Passing input audit: implemented direct-FDF input gates passed; scientific claim blocked.
- Passing run audit: implemented technical run gates passed; scientific claim blocked.
- Passing fixed-cell relax run: implemented technical plus fixed-cell force/marker gates passed; physical claim blocked.
- Stable evidence-bound series: numerical convergence candidate for the named observable/tolerance.
- Documented-only task package: eligible for manual evidence review, never an automated pass.
- Scientific acceptance: requires independently supported task and physical/model evidence.
