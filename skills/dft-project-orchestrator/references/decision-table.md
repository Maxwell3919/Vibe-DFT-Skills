# Mechanical orchestration decision table

The canonical machine-readable policy is [weak-model-decision-table.json](weak-model-decision-table.json). This Markdown projection must not override it.

Evaluate rows from top to bottom and stop at the first matching row. Emit exactly the listed finding and minimum next action. Do not continue to a later, more permissive row.

| Priority | Observable condition | State | Finding | Unique minimum next action | Maximum action |
| ---: | --- | --- | --- | --- | --- |
| 1 | Input is symlink/hardlink, changes during read, exceeds limit, has BOM/duplicate key/NaN/trailing document, or is not one object | invalid | `ORCH.JSON.INVALID` | `replace-input-with-one-stable-single-link-strict-json-object` | inspect-only |
| 2 | Contract/version/required field/ID is invalid or a record ref does not bind exact target bytes | invalid | `ORCH.CONTRACT.INVALID` or `ORCH.IDENTITY.MISMATCH` | `repair-first-invalid-field-or-exact-byte-reference` | inspect-only |
| 3 | Step ID is duplicated, dependency is unresolved, or graph is cyclic | invalid | `ORCH.DAG.DUPLICATE_STEP`, `ORCH.DAG.UNKNOWN_DEPENDENCY`, or `ORCH.DAG.CYCLE` | `repair-first-reported-dag-defect` | plan-only |
| 4 | Any required operation route is development, planned, or unsupported | blocked | `ORCH.ROUTE.NOT_ACTIVE` | `promote-through-governance-or-replace-first-nonactive-route` | plan-only |
| 5 | A ready step has an incomplete dependency, blocker, or nonpassing gate | blocked | `ORCH.STEP.NOT_READY` | `resolve-first-readiness-dependency-or-gate` | plan-only |
| 6 | Side-effecting step lacks human-decision, lease, side-effect, or scope policy | blocked | `ORCH.AUTH.POLICY_MISSING` | `add-bounded-human-decision-and-single-use-lease-policy` | plan-only |
| 7 | Execution decision is non-human, denied/deferred, expired, scope-mismatched, or hash/evidence-mismatched | blocked | `ORCH.AUTH.NOT_GRANTED` or `ORCH.AUTH.SUBJECT_MISMATCH` | `obtain-new-human-decision-for-exact-request-bytes` | request-execution-authorization |
| 8 | Scheduler fact exists but process or application fact is absent/conflicting | blocked | `ORCH.STATE.CONFLATED` | `collect-first-missing-independent-runtime-observation` | inspect-only |
| 9 | Technical run is complete but observable-specific convergence/claim evidence is absent | blocked | `ORCH.SCIENCE.NOT_REVIEW_READY` | `produce-first-missing-observable-specific-evidence` | postprocess-only |
| 10 | Evidence map is review-ready but no exact hash-linked expert decision exists | review required | `ORCH.SCIENCE.HUMAN_DECISION_MISSING` | `request-separate-human-scientific-review` | eligible-for-expert-review |
| 11 | No earlier condition can be established from exact evidence | blocked | `ORCH.EVIDENCE.INSUFFICIENT` | `collect-minimum-exact-evidence-for-first-applicable-orchestration-gate` | inspect-only |

Row 11 is the fail-closed default and has no required-evidence prerequisite. No row grants execution, lease issuance, route activation, or scientific acceptance. A report itself is unsigned; downstream evidence must bind the exact report bytes through a trusted external manifest.
