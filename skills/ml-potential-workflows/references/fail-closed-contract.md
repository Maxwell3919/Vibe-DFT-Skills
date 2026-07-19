# Fail-closed contract

## Evidence ladder

1. `inventory_only`: unverified prose and filenames.
2. `dataset_manifest_consistent`: metadata and split gates pass; referenced bytes are
   not authenticated by this candidate.
3. `training_plan_frozen`: provider, data, seeds, loss, stopping, metrics, and
   environment are explicit.
4. `training_run_external`: an authorized provider adapter may later execute; this
   candidate cannot.
5. `model_lineage_consistent`: artifact identity and provenance manifest pass without
   loading the artifact.
6. `evaluation_candidate`: frozen independent-test metrics pass every predeclared
   threshold and slice gate.
7. `deployment_handoff_candidate`: domain, monitoring, rollback, and authorization
   references pass local checks.
8. `expert_acceptance_external`: a human/platform decision remains required.

The development lifecycle caps all current reports at `no_positive_claim`.

## Gate precedence

1. Invalid, conflicting, leaked, unsupported, or threshold-failing evidence produces
   `local_gate_blocked`.
2. Absent manifest, hash, unit, split, protocol, source acceptance, provider identity,
   evaluation slice, OOD result, license, or domain record produces `needs_evidence`.
3. All local pre-execution gates passing with no execution receipt produces
   `needs_authorization`.
4. A valid deployment envelope with external authorization reference is at most
   `handoff_ready`; this candidate still cannot execute it.
5. Local metadata consistency is `local_gate_passed_limited` only.

## Stable exit codes

- `0`: implemented local checks passed; no execution or positive claim follows.
- `2`: input is malformed, incomplete, unsafe, inconsistent, unsupported, or failed a
  declared threshold.

## Privacy and safety

- Anchor each evidence path at a retained root descriptor, traverse every directory
  with no-follow `openat`, and open the final component once with
  `O_NONBLOCK|O_NOFOLLOW`. Hash and parse the same bounded bytes; reject symlinks,
  hardlinks, special files (including FIFOs), intermediate-directory swaps,
  final-identity drift, invalid UTF-8, duplicate keys, non-finite JSON and oversize
  data.
- Reports are create-only. Publication retains the output-directory and staging-file
  descriptors, requires an absent target, uses an atomic no-replace hard link, and
  verifies descriptor/name identities and payload bytes before and after linking.
  Existing or concurrently created reports remain unchanged, evidence aliases are
  refused, and path replacement is never used.
- Never deserialize model/checkpoint/archive bytes.
- Reports expose safe labels, hashes, counts and bounded metrics, not structures,
  labels, host paths, commands, credentials, proprietary data or model weights.
- No model response may self-author a reference-data acceptance, license, execution
  authorization, or scientific decision and then consume it as external trust.
- Downstream commands require the exact canonical upstream report shape, pass gates,
  action state, claim ceiling, evidence inventory, observations and limitations.
  This rejects partial forged pass records but does not authenticate a complete
  lookalike; production activation still requires a trusted bundle/signature layer.
- Fine-tune and pretrained modes bind distinct parent-model artifact and parent-model
  record hashes. A pretrained audit must identify the same artifact and record; a
  fine-tune output remains separate from its parent.
- Evaluation keeps model/dataset/plan/evaluator/slice/threshold hashes in distinct
  roles; deployment likewise keeps model/evaluation/adapter/rollback/authorization
  hashes distinct. Reusing one syntactically valid hash across trust roles blocks.
