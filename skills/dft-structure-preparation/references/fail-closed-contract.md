# Fail-closed contract

## Stable exits

| Exit | Meaning | Allowed claim |
|---:|---|---|
| `0` | Requested deterministic operation completed and emitted schema-shaped JSON | Candidate-local evidence only; current claim remains `no_positive_claim` |
| `2` | Input, policy, readiness, mapping, round-trip, or output-safety gate blocked | No positive result claim |
| `3` | A pinned optional provider is absent or version-mismatched | Metadata probe only; no backend operation claim |
| `4` | Unexpected internal failure | No result was certified |

Always parse the JSON report or the structured stderr finding. Do not infer success from an empty
stderr or from file creation.

## Refusal rules

Refuse and emit no certified result when any of these conditions holds:

- unreadable, non-regular, symlinked, identity-changing, oversized, non-UTF-8, duplicate-key,
  non-object, or non-finite input;
- unknown fields, missing fields, unsafe IDs, duplicate site IDs, unknown elements, invalid or
  overfull occupancies;
- invalid or blocked upstream `structure-manifest@1.0`, missing/mismatched identity preimage,
  inconsistent published cell/coordinates, existing unadapted transformation lineage, or
  occupancy/disorder that the staging contract cannot preserve;
- structure-kind/PBC/cell mismatch, singular cell, or coordinate representation mismatch;
- symmetry claims without required scope, tolerance, backend, or version;
- invalid molecular charge/multiplicity parity;
- incomplete reorder sets, invalid supercell matrices, unsupported operations, failed identity
  invariants, excessive strain/repeat/atom budgets, incompatible slab axes, unmatched interface
  cells, out-of-cell guests, or derived interatomic distances below the explicit hard gate;
- existing or evidence-alias output, unsafe or changing output parent, or failed atomic publish;
- missing/mismatched pinned provider when backend evidence is requested.

## Authority rules

The CLI may validate and transform its candidate-local normalized structure. It may not:

- activate this skill or promote registry/interface entries;
- execute a DFT engine or choose scientific calculation parameters;
- infer unreported symmetry, oxidation states, bonds, disorder orderings, charge, or spin;
- infer a Miller face, termination, interstitial, adsorption site, registry, molecular orientation,
  charge compensation, or stable structure from a geometric construction;
- describe a dependency probe as import, execution, integration, or license evidence;
- mark any structure scientifically accepted.

## Output safety

Outputs contain content-derived source labels, byte counts, and SHA-256 values instead of user
filenames or absolute paths. Input bytes are read once through an `O_NOFOLLOW` descriptor with a
bounded read, `fstat`, final `lstat`, and size/mtime/link-count identity checks. File outputs are
fully written and synchronized to a private temporary inode, then published with a same-directory
no-replace hard link. Existing paths, symlink aliases, hardlink aliases, and concurrent target
creation are never overwritten.

Every success and structured error envelope fixes `claim_ceiling=no_positive_claim`,
`promotion_authorized=false`, and `execution_authorized=false`. `future_gate_ceiling` is only a
promotion target and does not authorize routing, execution, or scientific use.
