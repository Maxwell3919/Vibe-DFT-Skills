# LAMMPS fail-closed contract

LAMMPS input is executable. This candidate statically recognizes only a conservative declarative MD subset. It separates script safety, release/build identity, package/style capability, units, topology, potential provenance, integration, initial state, restart lineage, output completion, trajectory integrity, sampling sufficiency, and expert scientific acceptance.

The Python guard binds each request/evidence base to a retained directory descriptor, opens every path component relative to it with `O_DIRECTORY|O_NOFOLLOW`, and opens the final name with `O_NONBLOCK|O_NOFOLLOW`. It accepts only bounded single-link regular files and verifies directory and file identity around the read, so directory/symlink substitution and FIFOs fail without blocking. A platform without the required descriptor-relative primitives is incomplete. The guard resolves only literal in-root includes, emits stable sorted JSON without timestamps or absolute paths, and never executes external software. Exit codes are `0` pass, `2` blocked, `3` incomplete, and `4` internal error. Dynamic constructs, unknown syntax, binary restarts, and unsupported trajectory variants cannot be converted to pass by assumption.

Downstream reports require passing upstream reports loaded from one bounded, no-follow, identity-stable raw snapshot. The loader validates the complete command-specific canonical shape, tool/engine/schema/command identity, decision consistency, development lifecycle, no-positive ceiling, false authorization fields, `report_authenticity=unsigned-candidate-output`, and self fingerprint. Every downstream `upstream` value binds the SHA-256 of those exact raw bytes, so canonically equivalent JSON with different raw bytes is a different lineage artifact. The self `report_fingerprint` detects semantic inconsistency but is never an origin or authorization trust root. Only a trusted manifest or signature verified outside this development Skill may attest report origin; without it, the report remains an unsigned local audit artifact.

Every current report has `claim_ceiling=no_positive_claim` and `report_authenticity=unsigned-candidate-output`; `promotion_ready`, `promotion_authorized`, and `execution_authorized` are false. The table records future gate potential only.

| Command | Future gate ceiling after promotion |
|---|---|
| `plan` | `no_positive_claim` |
| `audit-input` | `input_gates_only` |
| `audit-output` | `technical_run_gates_only` |
| `audit-trajectory` | `technical_run_gates_only` |

Current passing coverage is one project-authored `units lj`/atomic/LJ-cut/NVE/orthogonal/text-dump fixture. A pass does not raise the current candidate claim and does not establish physical validity, equilibrium, reproducibility across layouts, or publication readiness.

Report publication retains the staging file descriptor, verifies its regular-file identity, link count, size, and payload before and after publication, and uses a same-directory hard link as atomic create-if-absent. Replace semantics are forbidden. If any post-link check fails, cleanup unlinks the target only while it still matches the exact inode created by that call; a late, independently created, or substituted target is preserved.
