# Fail-closed contract

## State ladder

1. `inventory_only`
2. `layout_metadata_consistent`
3. `training_projection_frozen`
4. `render_and_execution_external`
5. `technical_run_record_consistent`
6. `frozen_model_lineage_consistent`
7. `generic_evaluation_required`
8. `expert_acceptance_external`

No stage implies the next. Development lifecycle caps every report at
`no_positive_claim`.

## Failure precedence

- Invalid/mismatched type maps, shapes, units, hashes, groups, splits, version,
  backend, seed, loss, steps, run status or model lineage: `local_gate_blocked`.
- Missing referenced evidence, provider schema, environment, checkpoint, run,
  evaluation, OOD, license or external decision: `needs_evidence`.
- All pre-execution metadata gates passing: `needs_authorization`; this candidate has
  no execution action.
- A local metadata audit pass only: `local_gate_passed_limited`.

## I/O and privacy

- Anchor each evidence path at a retained root descriptor, traverse every directory
  with no-follow `openat`, and open the final component once with
  `O_NONBLOCK|O_NOFOLLOW`. Strict bounded JSON rejects duplicate keys, BOM,
  NaN/Infinity, symlinks, hardlinks, special files (including FIFOs), oversize input,
  intermediate-directory swaps and final-identity drift.
- Hash and parse one exact byte snapshot.
- Reports are create-only. Publication retains the output-directory and staging-file
  descriptors, requires an absent target, uses an atomic no-replace hard link, and
  verifies descriptor/name identities and payload bytes before and after linking.
  Existing or concurrently created reports remain unchanged, evidence aliases are
  refused, and path replacement is never used.
- Never open NPY, checkpoint, model, log archive, pickle or provider package bytes.
- Reports exclude system paths, raw arrays, structures, labels, commands,
  environment variables and secrets.
- Downstream commands require the exact canonical upstream report shape, pass gates,
  action state, claim ceiling, evidence inventory, observations and limitations.
  This blocks partial forged reports but cannot authenticate a complete lookalike;
  production activation requires a trusted bundle/signature resolver.

## Exit codes

- `0`: requested local metadata gates passed; no execution or positive claim.
- `2`: malformed, missing, unsafe, unsupported or inconsistent evidence.
