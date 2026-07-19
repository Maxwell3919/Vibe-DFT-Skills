# GPUMD fail-closed contract

This candidate separates claim definition, official-version evidence, environment readiness, input grammar, potential provenance, initial state, run-block semantics, restart lineage, technical completion, trajectory integrity, statistical sufficiency, and expert scientific acceptance.

## Deterministic boundary

`gpumd_guard.py` reads bounded ASCII or strict JSON regular files, refuses symlinks and report overwrite, emits sorted stable JSON with no timestamps or absolute paths, and never launches external software. It opens every ancestor component relative to a stable directory descriptor with no-follow semantics, opens final inputs nonblocking before checking regular-file identity, and binds all same-directory evidence reads to that stable anchor. Reports are written through a retained staging descriptor and published by atomic hard-link create-if-absent after before/after inode, size, and content checks; replacement publication is forbidden. Exit codes are `0` pass, `2` blocked, `3` incomplete, and `4` internal error.

An incomplete finding cannot be converted to pass by assuming a default. A downstream audit loads exact upstream raw bytes through the identity-checked single-FD reader, validates the complete command-specific report shape and development/no-positive/false-authorization invariants, and binds the SHA-256 of those exact bytes. The self-computed canonical JSON `report_fingerprint` is checked for consistency but is not a trust root; semantic equivalence after any raw-byte change does not preserve lineage.

## Supported slice

Only GPUMD v5.3 standard MD using a single analytic LJ potential is parser-supported. Each run block must explicitly set an ensemble and all non-propagating output controls. Inputs outside the allowlist are incomplete, not guessed. Output fixtures are project-authored legal synthetic artifacts, not evidence of a real engine run.

## Current ceiling and future gate potential

Every current report has `claim_ceiling=no_positive_claim`, `report_authenticity=unsigned-candidate-output`, and false promotion/execution booleans. A candidate can compute a structurally complete report and its own fingerprint, but that does not authenticate its producer. Only an external trusted manifest or signature under separate control can promote such bytes to authenticated evidence. The table is emitted only as `future_gate_ceiling` potential after a separate atomic promotion.

| Command | Future gate ceiling |
|---|---|
| `plan` | `no_positive_claim` |
| `audit-input` | `input_gates_only` |
| `audit-output` | `technical_run_gates_only` |
| `audit-trajectory` | `technical_run_gates_only` |

A pass never raises the current candidate claim. It also never establishes model suitability, equilibrium, ergodicity, scientific novelty, or publication readiness. Human scientific acceptance is external.

## Promotion blockers

Activation requires version-matched legal real artifacts, independent integration on a supported GPU environment, source-registry license reconciliation, shared interface alignment, adversarial review, and registry promotion. The candidate cannot self-promote or self-authorize execution.
