# Fail-closed contract

## Input boundary

The CLI accepts bounded UTF-8 JSON requests and bounded text artifacts. It retains the request parent directory descriptor as the evidence root, traverses every relative parent with `openat(O_DIRECTORY|O_NOFOLLOW)`, opens the final component once with `O_NONBLOCK|O_NOFOLLOW`, reads only through that descriptor, and binds pre/post `fstat` to anchored and lexical final `lstat` evidence, including device, inode, size, modification/change time, and link count. It rejects duplicate JSON keys, non-finite JSON numbers, UTF-8 BOM input, symlinks, hardlinks, special files, oversized files, files, roots, or intermediate path identities that change during the read, absolute or traversal paths, path-like private strings, and secret-bearing keys. Reports contain safe labels and SHA-256 values, never resolved private paths.

Every successfully read request/evidence identity is retained in process memory until output installation. An output is rejected when its lexical/resolved path or device/inode aliases any input, including symlink and hardlink aliases. Existing targets are never overwritten; the compatibility `--overwrite` flag fails closed. Report bytes are written through a retained private same-directory descriptor, reread to verify the payload hash, and fsynced. Publication uses `os.link` as atomic create-if-absent, verifies both names and the retained descriptor at the transient two-link state, retires the private name, and rechecks the final single-link inode, size, and payload before directory fsync. Late target creation is never overwritten, and failed staging or publication leaves no accepted report.

The candidate never reads `POTCAR` contents, never stores a LOBSTER binary or basis resource, never imports an artifact as Python, and never invokes an external command.

## Required identities

An audit request binds:

- exact provider `LOBSTER 5.1.1` and environment profile `lobster-5`;
- evidence class (`synthetic-fixture` or `real-artifact`);
- immutable parent-record file and SHA-256 plus an independent validation-receipt file and SHA-256;
- DFT code/version/task/protocol, structure fingerprint, wavefunction artifact label/hash, and exact structure/k-point/settings/potential-metadata hashes;
- parent input, completion, numerical, and wavefunction-eligibility gates, duplicated in a receipt bound to separate evidence hashes;
- execution record ID plus validation receipt, parent, DFT protocol/input identities, structure, wavefunction, and `lobsterin` hashes;
- basis family/source and the per-element orbital map;
- each required artifact role, safe relative file, and content hash;
- user-declared spilling, projected-band completeness, Fermi alignment, curve-integral, and DOS-closure tolerances;
- requested claims.

The synthetic parent contract is candidate-local. It must not be represented as the planned shared `electronic-wavefunction-source@1.0` interface.

## Gate states

Every gate is exactly `pass`, `fail`, `blocked`, or `not_evaluated`. A downstream gate cannot pass when an upstream identity or artifact gate fails.

| Gate | Pass evidence | Fail or block condition |
|---|---|---|
| provider | exact version/profile and recognized output header | unknown/drifted version or missing real authorization |
| parent | parent and independent receipt hashes plus all duplicated DFT identities agree | missing/detached receipt, self-reported pass only, unsupported provider, non-passing gate, mismatch |
| execution binding | execution identity agrees with receipt, parent protocol/inputs, wavefunction, and structure | absent or mismatched binding |
| artifact | every task-required role is regular, bounded, hash-matched | missing, unsafe, unreadable, or mismatched file |
| completion | recognized completion marker and no fatal marker | truncation, fatal marker, or missing marker |
| basis | declared and observed per-element orbitals agree exactly | missing element/orbital, source ambiguity, mismatch |
| projection | both absolute spillings and projected-band/window/Fermi evidence exist and meet declared limits | absent, non-finite, negative, incomplete, or over threshold |
| curve | explicit kind/unit/Fermi reference/spin/sign, finite monotonic grid | unknown format/convention or malformed data |
| consistency | curve Fermi/window agrees with projection evidence and integrated curve or projected-DOS closure meets tolerance | detached reference or failed numerical closure |
| task | selected task profile is complete | unsupported task or missing required role |
| claim | claim is no stronger than evidence and candidate maturity | chemical interpretation requested as an automatic conclusion |

## Status and exit mapping

- `passed` / exit `0`: all selected synthetic candidate gates passed.
- `invalid_input` / exit `2`: request safety or contract failure.
- `blocked_external_evidence` / exit `3`: license, provider route, genuine artifact maturity, shared interface, or expert interpretation is absent.
- `parse_failed` / exit `4`: a declared artifact does not match the selected parser profile.
- `failed` / exit `5`: evidence was parseable but a scientific-technical gate failed.

The status is deterministic: invalid input outranks parse failure; parse failure outranks failed gates; failed gates outrank external blockers.

The canonical weak-model routing policy is [weak-model-decision-table.json](weak-model-decision-table.json), validated as shared `candidate-decision-table@1.0`. It is the only machine source of truth: select the first ascending-priority match and use the final evidence-free fail-closed default when no earlier condition is established.

## Claim ceiling

At current development/non-routable maturity, every report is limited to `no_positive_claim`, including synthetic passes. Real-artifact requests are explicitly blocked until real forward validation is accepted. No report from this candidate can set `scientific_acceptance`, and no later adapter may upgrade a claim merely because plotting succeeded.
