# Fail-closed HPC execution contract

## Absolute prohibitions in candidate state

No process spawn, shell evaluation, SSH, socket, scheduler command, remote API, credential lookup, environment-variable secret read, file staging, output collection, job submission, job control, or local calculation execution is permitted. Dry-run rendering is data transformation only.

## Ordered gates

| Gate | Pass evidence | Failure result | Minimum next action |
| --- | --- | --- | --- |
| Strict input | Stable dirfd component walk and one single-link regular non-FIFO UTF-8 JSON object within 1 MiB | `HPC.JSON.INVALID` | Replace the first malformed or unstable input |
| Request identity | `execution-request@1.0`, safe IDs, exact raw-byte digest | `HPC.REQUEST.INVALID` | Regenerate the immutable request |
| Command | argv-only, shell false, bounded secret-free items, non-shell executable | `HPC.COMMAND.UNSAFE` | Replace with a direct executable argv |
| Inputs/outputs | Present inputs have exact hashes; outputs start missing and named | `HPC.ARTIFACT.INVALID` | Restage and rehash the first invalid artifact |
| Profiles/resources | Registered IDs and positive bounded resources | `HPC.PROFILE.UNRESOLVED` | Select a reviewed environment and scheduler profile |
| Human decision | Human approval for exact request hash, evidence, scope, side effects, and time | `HPC.AUTH.NOT_GRANTED` | Obtain a new exact-request authorization |
| Lease | Active, unexpired, single-use, exact request/decision/hash/resource binding | `HPC.LEASE.INVALID` | Issue a new bounded lease from the approved request |
| Idempotency | No prior consumption or uncertain matching attempt | `HPC.IDEMPOTENCY.BLOCKED` | Reconcile the previous attempt before proceeding |
| Renderer | Supported family, scheduler arithmetic valid, site policy explicit | `HPC.SCHEDULER.UNSUPPORTED` | Select a supported reviewed profile |
| Scheduler observation | Native code with source/version evidence | `HPC.STATUS.UNKNOWN` | Collect an authoritative scheduler observation |
| Process observation | Return/signal/timeout evidence independent of scheduler | `HPC.PROCESS.UNKNOWN` | Collect launcher/process evidence |
| Application observation | Code-specific completion/failure evidence | `HPC.APPLICATION.UNKNOWN` | Run the engine-specific output gate |
| Scientific gate | Observable-specific numerical evidence | `HPC.SCIENCE.NOT_ASSESSED` | Hand off to the calculation/postprocess Skill |

## Exact-byte and subset rules

- Record-ref SHA-256 covers the unchanged stored UTF-8 JSON bytes, including whitespace and final newline.
- Lease argv hash uses deterministic compact JSON encoding of the argv array, not shell text.
- Lease input hashes, output labels, environment profiles, scheduler profiles, side effects, and resources must be subsets or ceilings of the immutable request and authorization.
- Decision scope must match the request scope; an apparently broader approval is rejected rather than silently narrowed.
- A consumed, revoked, or expired lease is unusable. A lease authorizes at most one execution.

## Status lattice

Preserve three independent layers:

- Scheduler: `not-submitted`, `submitted`, `queued`, `running`, `succeeded`, `failed`, `cancelled`, `unknown`, `not-applicable`.
- Process: `not-started`, `running`, `exited-zero`, `exited-nonzero`, `signalled`, `timed-out`, `unknown`, `not-applicable`.
- Application: `not-started`, `running`, `completed`, `incomplete`, `failed`, `unknown`, `not-applicable`.

Normalize to `succeeded` only for scheduler `succeeded` or `not-applicable`, process `exited-zero`, and application `completed`. Any terminal failure layer yields failure/timed-out/cancelled as supported. Missing or conflicting terminal evidence yields blocked, never success.

## Retry, cancellation, and uncertain outcomes

- `automatic_retry` must be false.
- Resource, argv, input, environment, scheduler, side-effect, or output changes create a new request and usually a new authorization.
- Retry with unchanged request still needs a fresh single-use lease and an explicit attempt record.
- Cancellation is a side effect distinct from submission and needs `scheduler-control` authorization.
- A timeout while talking to a scheduler creates an uncertain outcome. Do not resubmit or cancel blindly; query authoritative state through a reviewed adapter and reconcile by idempotency key.

## Claim boundary

A dry-run render establishes only what text and argv the candidate would propose. It proves no scheduler acceptance, execution, application completion, numerical adequacy, or science. Candidate state remains `no_positive_claim`.

Candidate reports are deterministic but unsigned. They can be altered after emission; downstream evidence must hash the exact report bytes in a trusted external manifest or signed envelope before relying on them. The report's own narrative is not an authenticity proof.
