# Fail-closed orchestration contract

## Scope

The Skill may inspect supplied bytes, derive a plan or report in memory, and write only a new caller-selected output when a future reviewed adapter explicitly permits it. The candidate CLI is read-only and writes JSON only to stdout.

It may not execute calculation software, call a scheduler, connect to a remote host, obtain credentials, issue or consume a lease, modify registries, activate routes, or make a scientific decision.

## Ordered gates

| Gate | Pass evidence | Failure result | Minimum next action |
| --- | --- | --- | --- |
| Objective | Explicit objective, observables, protocol ID, and limits | `ORCH.OBJECTIVE.INCOMPLETE` | Supply the first missing objective field |
| Parse | Stable dirfd component walk, one single-link regular UTF-8 JSON object, bounded size, no FIFO/symlink/BOM/duplicate keys/NaN/trailing document | `ORCH.JSON.INVALID` | Replace the file with one stable strict JSON object |
| Contract | Exact contract name/version and required bounded fields | `ORCH.CONTRACT.INVALID` | Repair the first invalid field |
| Identity | Unique safe plan/step IDs and exact raw-byte hashes on refs | `ORCH.IDENTITY.MISMATCH` | Recompute the reference from unchanged target bytes |
| Routing | Every executable step names an active reviewed route | `ORCH.ROUTE.NOT_ACTIVE` | Promote the route through governance or replace the step |
| DAG | Dependencies exist, are unique, non-self, and acyclic | `ORCH.DAG.INVALID` | Remove the reported unresolved edge or cycle |
| Step readiness | Dependencies complete, required inputs present, gates pass, no blockers | `ORCH.STEP.NOT_READY` | Resolve the first named dependency/input/gate blocker |
| Authorization policy | Side-effecting steps require a human decision and single-use lease | `ORCH.AUTH.POLICY_MISSING` | Add a bounded authorization policy |
| Request | Exact plan/step binding, argv-only, shell false, hashes/resources/scopes bounded | `ORCH.REQUEST.INVALID` | Regenerate the immutable execution request |
| Human authorization | Human, approved, unexpired, exact request hash, matching scope and evidence | `ORCH.AUTH.NOT_GRANTED` | Obtain a new decision for the exact request |
| Runtime evidence | Scheduler, process, and application observations remain separate | `ORCH.STATE.CONFLATED` | Collect the missing independent observation |
| Numerical/scientific evidence | Observable-specific gates and limitations are recorded | `ORCH.SCIENCE.NOT_REVIEW_READY` | Produce the first missing numerical evidence |
| Acceptance | Separate human scientific decision resolves by exact hash | `ORCH.SCIENCE.HUMAN_DECISION_MISSING` | Request expert review; do not self-accept |

## Evidence rules

- Hash record references over exact stored bytes. Do not canonicalize, reserialize, trim, or normalize before hashing.
- A schema-valid placeholder digest is unresolved evidence.
- A plan must not point to an execution request generated from it; the request points to the immutable plan.
- A decision is not embedded into the request or lease. It is a separate record with its own exact-byte identity.
- Development, planned, or unsupported routes; cached documentation without version identity; narrative claims; screenshots without provenance; and a process return code alone cannot pass a decisive gate.
- If evidence conflicts, keep both facts, mark the gate blocked, and request reconciliation.

## State separation

Maintain these values independently:

- Workflow: `draft`, `ready`, `blocked`, `executing`, `completed`, `abandoned`.
- Step: `planned`, `ready`, `blocked`, `running`, `completed`, `failed`, `skipped`.
- Scheduler: not submitted, queued, running, terminal, unknown.
- Process: not started, running, exited zero/nonzero, signalled, timed out, unknown.
- Application: not started, running, completed, incomplete, failed, unknown.
- Scientific acceptance: `not_assessed`, `requires_human_review`, `accepted`, `rejected`.

No mapping between layers is automatic except a conservative failure propagation. Scheduler success may coexist with application failure; technical completion may coexist with inadequate numerical evidence; review eligibility is not acceptance.

## Retry, resume, and idempotency

- Use immutable request IDs plus exact-byte hashes as idempotency keys.
- Automatic retry is forbidden. A retry requires a new attempt record and an explicit decision when scope, inputs, argv, resources, or limits change.
- Resume only from validated persisted records/events. Conversation history is advisory, never authoritative state.
- Conflicting terminal events, duplicated sequence numbers, lease reuse, or an uncertain remote outcome block further side effects until reconciled.

## Claim ceiling

Candidate validation may establish only documented behavior of its own deterministic checks. Because the registry keeps this Skill in development and routing blocked, its operational claim ceiling remains `no_positive_claim`. Promotion and scientific acceptance are separate human-governed actions.

Candidate reports are deterministic but unsigned. They can be altered after emission; downstream evidence must hash the exact report bytes in a trusted external manifest or signed envelope before relying on them. The report's own narrative is not an authenticity proof.
