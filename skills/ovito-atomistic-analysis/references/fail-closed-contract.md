# Fail-closed contract

## Stable exits

| Exit | Meaning | Allowed claim |
|---:|---|---|
| `0` | Requested parser, planner, probe match, or bounded metadata execution completed | Candidate-local evidence only; current claim remains `no_positive_claim` |
| `2` | Input, source, mapping, edition, license, operation, authorization, or output gate blocked | No positive result claim |
| `3` | OVITO is absent, its version mismatches, or the required Python API is unavailable | Provider unavailability only |
| `4` | Unexpected internal failure | No result was certified |

Always inspect JSON output. Planning can exit zero with execution readiness blocked. Inventory can
exit zero with analysis readiness blocked or requiring a decision. Use strict flags only at the
corresponding downstream boundary.

## Execution refusal

Refuse actual external execution unless all conditions hold:

- the user supplied `--authorize-execution` and the exact plan-emitted
  `--authorization-scope` for this invocation;
- inventory and pipeline JSON are strict, regular, immutable inputs;
- the execution source raw-byte hash equals the inventory and pipeline source hash;
- every selected frame is within the inventory;
- provider profile is Basic and both distribution metadata and imported module report exact
  version `3.15.5`;
- every operation is candidate-implemented `compute-frame-metadata`;
- no parser, topology, periodicity, edition, entitlement, or planning blocker remains;
- the requested output does not exist or alias any evidence and its parent is a real directory.

Pro execution is always refused by this candidate. A flag cannot grant a commercial entitlement.

## No-result rules

- A parser inventory contains no OVITO result.
- A pipeline plan contains no numerical values or rendered artifact.
- A metadata probe contains no module import, pipeline execution, or license verification.
- A failed execution contains no certified partial frame set.
- A synthetic API double used by tests is invocation evidence, not tool-integration evidence.
- A completed metadata execution contains no coordination, defect, strain, dislocation, or
  rendering result.

## Filesystem and privacy rules

Refuse symlink or identity-changing inputs and symlink/existing/hardlink-alias outputs. Input bytes
are read once through an `O_NOFOLLOW` descriptor with bounded read, `fstat`, final `lstat`, and
size/mtime/link-count identity checks. The provider receives only a private temporary snapshot of
those already verified bytes, preventing source-path TOCTOU drift. The snapshot is reparsed and
compared with the supplied inventory before provider import, so a self-consistent but forged
inventory record cannot authorize execution. File outputs are synchronized
to a private temporary inode and atomically published through a same-directory no-replace hard
link; failure leaves no certified partial result.

Emit only content-derived source labels, byte counts, and hashes; never place user source names or
absolute host paths in JSON artifacts. Do not copy trajectories into the repository. Treat trajectories,
entitlement material, and activation material as private inputs.

Every success and structured error envelope fixes `claim_ceiling=no_positive_claim`,
`promotion_authorized=false`, and `execution_authorized=false`. The CLI authorization receipt is
invocation-scoped and separate from those lifecycle fields. `future_gate_ceiling` is not current
promotion, execution, license, or scientific authority.
