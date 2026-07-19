# GROMACS fail-closed contract

## State ladder

| State | Required evidence | Maximum local conclusion | Hard block |
|---|---|---|---|
| `objective_defined` | anonymous IDs, version, task, claim, observable and tolerance | plan recorded | invented or absent value |
| `official_behavior_matched` | exact executable/manual version and decisive official pages | documented behavior | `current` projected backward, unknown build, unresolved source |
| `system_model_bound` | coordinate, topology include closure, force-field/model sources, licenses and hashes | model identity recorded | missing include, hash mismatch, unknown terms |
| `input_preflight_passed` | passing plan plus supported `.mdp`, `.gro`, `.top/.itp` core | eligible for authorized preprocessing | duplicate/unsupported syntax, unit/PBC/ensemble/seed/restart mismatch |
| `execution_complete` | passing input audit, one matching log, terminal step and no adverse marker | technical completion candidate | truncated/concatenated log, fatal/warning/step mismatch |
| `trajectory_integrity_passed` | content-bound frames, atom/site order, time, cell/PBC and segment lineage | trajectory inventory ready | discontinuity, topology mismatch, invalid time/cell |
| `sampling_candidate` | predeclared discard, production series, estimator, autocorrelation, ESS and uncertainty | numerical candidate only | post-hoc window, low ESS, uncertainty violation |
| `physical_validity_review` | model-domain, time-step/drift, finite-size, boundary and replica checks | eligible for expert review only | any relevant check unassessed |
| `scientific_acceptance` | independent human decision record | bounded accepted claim | never produced by this candidate |

Do not skip a state. `pass` is local; missing evidence is `incomplete`, not permission to infer.

## Deterministic report contract

Every command emits UTF-8 JSON with stable keys including `candidate_lifecycle`, current `claim_ceiling`, descriptive `future_gate_ceiling`, `promotion_ready`, `promotion_authorized`, `execution_authorized`, `report_authenticity`, `decision`, `maturity`, `findings`, `evidence`, `metrics`, and `limitations`. While this directory is in development, `claim_ceiling=no_positive_claim`, `report_authenticity=unsigned-candidate-output`, and all authorization/promotion booleans remain false even when an offline gate passes. Findings use catalog codes and include `gate`, `severity`, `message`, and `next_action`. Reports contain basename labels and SHA-256, never private absolute paths.

Load an upstream report from one bounded, no-follow, identity-stable raw snapshot. Validate its complete command-specific canonical shape, tool/engine/schema/command identity, decision consistency, development lifecycle, no-positive ceiling, false authorization fields, unsigned authenticity marker, and self fingerprint. Bind every downstream `upstream` entry to the SHA-256 of those exact raw bytes and compare raw hashes at every handoff. Canonically equivalent JSON with different raw bytes is a different lineage artifact. The self `report_fingerprint` detects semantic inconsistency but is never an origin or authorization trust root. Only a trusted manifest or signature verified outside this development Skill may attest origin; absent that external evidence, the report is only an unsigned local audit artifact.

Exit codes are `0=local pass`, `2=blocked or failed`, `3=incomplete or unsupported`, and `4=internal error`. A report is authoritative over the one-line terminal summary.

## Input policy

Bind each request/evidence base to a retained directory descriptor. Open every path component relative to that descriptor with `O_DIRECTORY|O_NOFOLLOW`, then open the final name with `O_NONBLOCK|O_NOFOLLOW`. Accept only a bounded regular file with link count one, and verify the directory and file identities before and after reading. A symlink swap, directory substitution, FIFO, device, socket, hard-linked input, or identity/size drift fails closed; a platform without the required descriptor-relative primitives is incomplete.

- Accept only a conservative core of literal `.mdp` assignments. Duplicate fields are ambiguous and fail.
- Resolve only quoted topology includes that remain under the declared topology root. Reject cycles and path escape. Treat angle-bracket, macro-dependent, or generated includes as incomplete.
- Require a provenance manifest that exactly covers the coordinate, root topology, every resolved include, and any parent checkpoint used. Recompute all hashes.
- Require explicit GROMACS units in the plan and reject external-unit substitution.
- Require `gen-vel=yes` plus explicit nonnegative `gen-seed` for a new generated-velocity run. Require `continuation=yes`, `gen-vel=no`, parent ID, and checkpoint hash for checkpoint continuation.
- Never invoke `gmx grompp`; never accept `-maxwarn`; never infer processed TPR content from text inputs.

## Output and statistics policy

- Require exactly one version banner and one `Finished mdrun` terminal marker, no `Fatal error`, constraint warning, `NaN`, signal, or early-step mismatch.
- Bind the log and series to the passing input-audit content hash.
- Analyze only observables named in the plan. Discard only the predeclared equilibration steps.
- Estimate uncertainty with deterministic block means and report lag autocorrelation/ESS. The method is a screening gate, not a universal statistical proof.
- Never turn stable energy, temperature, density, or pressure alone into physical validation.

## Trajectory policy

The offline parser supports text `.gro` frame sequences only. XTC/TRR/TNG/H5MD require a future version-pinned official adapter. For `.gro`, require finite coordinates and box, constant atom count/order, monotonic explicit time, plan-compatible cadence, and no claim of unwrapped coordinates. A trajectory audit cannot create missing upstream records required by `atomistic-trajectory-manifest@1.0`.

## Side-effect policy

Only read supplied artifacts and write a new report path. Refuse symlinks, oversized inputs, path escape and report overwrite. Retain the staging file descriptor through publication; verify its regular-file identity, link count, size, and payload before and after an atomic same-directory hard-link create-if-absent. Never replace an existing target. If publication later fails, unlink the report name only while it still matches the exact inode installed by this call; preserve every independently created or substituted target. Do not execute GROMACS, a scheduler, shell, remote connection, package manager, or network operation. External execution requires a separate authorization record and future execution adapter.
