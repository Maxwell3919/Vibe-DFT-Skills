# Mechanical HPC execution decision table

The canonical machine-readable policy is [weak-model-decision-table.json](weak-model-decision-table.json). This Markdown projection must not override it.

Evaluate rows from top to bottom and stop at the first match. Emit exactly the listed finding and minimum next action. A later row cannot override an earlier blocker.

| Priority | Observable condition | State | Finding | Unique minimum next action | Maximum action |
| ---: | --- | --- | --- | --- | --- |
| 1 | Input is symlink/hardlink, changes during read, exceeds limit, has BOM/duplicate key/NaN/trailing document, or is not one object | invalid | `HPC.JSON.INVALID` | `replace-first-input-with-one-stable-single-link-strict-json-object` | inspect-only |
| 2 | Request contract is invalid or uses a shell/eval, unsafe executable, control character, secret-like value, absolute/private path, missing input hash, or present expected output | invalid | `HPC.REQUEST.INVALID`, `HPC.COMMAND.UNSAFE`, or `HPC.ARTIFACT.INVALID` | `regenerate-direct-argv-request-and-restage-first-invalid-artifact` | inspect-only |
| 3 | Environment/scheduler profile is absent, non-synthetic in candidate mode, family-mismatched, or version-unresolved | blocked | `HPC.PROFILE.UNRESOLVED` or `HPC.SCHEDULER.UNSUPPORTED` | `select-one-reviewed-compatible-environment-and-scheduler-profile` | plan-only |
| 4 | Human decision is missing/non-human/denied/expired/scope-mismatched or does not bind exact request bytes | blocked | `HPC.AUTH.NOT_GRANTED` or `HPC.AUTH.HASH_MISMATCH` | `obtain-new-human-authorization-for-exact-request-bytes` | request-execution-authorization |
| 5 | Lease is expired/revoked/consumed, reusable, broadened, or hash-mismatched | blocked | `HPC.LEASE.INVALID` or `HPC.IDEMPOTENCY.BLOCKED` | `issue-one-fresh-non-broadening-single-use-lease` | plan-only |
| 6 | Submission renderer receives anything other than exact `scheduler-submit` scope | blocked | `HPC.AUTH.NOT_GRANTED` | `route-control-request-away-from-submission-renderer` | plan-only |
| 7 | A matching prior submission outcome is unknown or the lease is already consumed | blocked | `HPC.IDEMPOTENCY.BLOCKED` | `reconcile-authoritative-prior-attempt-before-any-new-side-effect` | inspect-only |
| 8 | Cancellation/restart is requested without matching `scheduler-control`/fresh-submit authorization and lineage | blocked | `HPC.AUTH.NOT_GRANTED` | `obtain-action-specific-control-or-restart-decision-and-fresh-lease` | plan-only |
| 9 | Status contract is invalid or native and normalized scheduler/process/application/return-code values conflict | invalid | `HPC.STATUS.UNKNOWN`, `HPC.PROCESS.UNKNOWN`, or `HPC.APPLICATION.UNKNOWN` | `repair-first-invalid-or-conflicting-status-field` | inspect-only |
| 10 | Status contract is valid but a terminal scheduler, process, or application observation is unknown or absent | blocked | `HPC.STATUS.UNKNOWN`, `HPC.PROCESS.UNKNOWN`, or `HPC.APPLICATION.UNKNOWN` | `collect-engine-specific-process-and-application-completion-evidence` | inspect-only |
| 11 | The classifier establishes a scheduler, process, or application terminal failure; classifier exit 0 is command success only | failed | `HPC.RUNTIME.FAILED` | `preserve-failed-artifacts-and-diagnose-first-engine-specific-failure` | inspect-only |
| 12 | Scheduler succeeded/not-applicable, process exited zero, and application completed | technical candidate | none | `handoff-to-rigorous-engine-output-and-numerical-gates` | postprocess-only |
| 13 | No earlier condition can be established from exact evidence | blocked | `HPC.EVIDENCE.INSUFFICIENT` | `collect-minimum-exact-evidence-for-first-applicable-hpc-gate` | inspect-only |

Row 13 is the fail-closed default and has no required-evidence prerequisite. Even row 12 does not establish numerical adequacy or scientific acceptance. Rendering and status classification perform no side effect. Reports are unsigned and require exact-byte binding by a trusted external manifest before evidentiary use.
