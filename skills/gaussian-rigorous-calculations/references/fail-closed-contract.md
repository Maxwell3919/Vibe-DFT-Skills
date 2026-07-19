# Fail-closed contract

## State machine

The candidate uses the following monotonic states:

1. `inventory_only`: prose and filenames have no positive evidentiary value.
2. `plan_validated`: all explicit plan fields are structurally valid.
3. `input_gates_passed`: implemented input parser gates match the exact plan bytes.
4. `execution_external`: execution is outside this candidate and requires a separate
   licensed, authorized platform record.
5. `technical_run_gates_passed`: exact input/output bytes, revision, termination,
   energy, and requested task markers passed.
6. `task_candidate`: stationary-point evidence matches the narrow task profile.
7. `expert_review_required`: scientific acceptance remains external.

No state may be inferred from a later state name, a filename, an image, or user prose.
The development lifecycle caps the public claim at `no_positive_claim` even when local
deterministic checks pass.

## Mandatory gates

| Gate | Pass evidence | Block examples | Maximum future meaning |
|---|---|---|---|
| plan-integrity | Strict JSON with every required field | defaulted method, basis, charge, tolerance, or version | no positive claim |
| input-identity | Exact SHA-256 and byte count | unreadable, linked, oversize, NUL, or changed input | input gate only |
| input-semantics | One supported route; exact plan match | unsupported feature, task mismatch, malformed geometry | input gate only |
| structure-lineage | Accepted molecular-structure manifest hash plus canonical explicit elements | missing manifest hash, invalid atom label, or detached geometry | input gate only |
| parent-lineage | Safe label and exact SHA-256 | `%OldChk`/read-from-checkpoint without parent record | input gate only |
| environment | Registered revision/profile plus external license attestation | unknown revision, unsupported host, missing attestation | documentary only |
| output-identity | Exact SHA-256 and byte count | unreadable, linked, oversize, or changed output | technical only |
| execution-record-binding | Strict external record binds exact plan/input/output, revision, environment, authorization, exit and checkpoint metadata | missing, malformed, detached or failed execution record | technical metadata only |
| completion | Matching revision, no error marker, one normal termination | mismatch, error termination, ambiguous/multiple termination | technical only |
| task-completion | Energy, no known SCF-failure sentinel, plus requested optimization/frequency evidence | absent energy, known SCF non-convergence, incomplete optimization, missing frequencies | technical only |
| stationary-point | Expected negative-frequency count | minimum with negatives or TS candidate not exactly one | numerical candidate only |
| scientific-acceptance | Independent expert decision over a complete evidence bundle | any self-declared verdict | eligible for expert review only |

## Failure precedence

Use the first applicable state:

1. `local_gate_blocked` for invalid input, unsupported feature, mismatch, error
   termination, ambiguous completion, or failed task rule.
2. `needs_evidence` for absent plan, input, output, hash-bound lineage, version, or
   environment record.
3. `needs_authorization` only when every local gate needed before execution passed and
   the next action is licensed execution.
4. `local_gate_passed_limited` only after the requested local deterministic command
   returned a pass report.

## Stable exit codes

- `0`: the requested local deterministic check completed and its implemented gates
  passed. The report still says `no_positive_claim` while in development.
- `2`: malformed request, missing evidence, blocked gate, unsupported feature, or I/O
  boundary failure.

No exit code authenticates the Gaussian installation, license, execution, checkpoint,
or scientific conclusion.

## Hash and privacy rules

- Hash exact raw bytes once and parse those same bytes.
- Anchor every request/evidence path at a retained root descriptor, traverse each
  directory with no-follow `openat`, and open the final component once with
  `O_NONBLOCK|O_NOFOLLOW`. Reject symlinks, hardlinks, special files (including
  FIFOs), oversize files, intermediate-directory swaps, final-identity drift,
  invalid UTF-8, duplicate JSON keys, NaN/Infinity, and NUL bytes.
- Reports are create-only. The writer retains the output-directory and staging-file
  descriptors, requires an absent target, publishes with an atomic no-replace hard
  link, verifies descriptor/name identities and payload bytes before and after
  publication, and never uses path replacement. An existing or concurrently created
  report is preserved; an output path that aliases evidence is rejected.
- Reports use basenames only and never echo input, output, route text, coordinates,
  title text, checkpoint paths, host paths, environment variables, or secret values.
- A checkpoint reference consists of a safe label and SHA-256. It does not expose or
  validate checkpoint contents.
- An execution record is strict external metadata, not self-proving trust. This
  candidate does not authenticate its issuer, environment, authorization, or
  checkpoint bytes; production activation requires a trusted bundle resolver.
