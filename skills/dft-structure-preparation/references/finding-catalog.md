# Stable finding catalog

Treat IDs as machine-facing identifiers. Messages may become clearer; ID meaning and exit class
must remain stable within schema version 1.0.

## Input and schema blockers

`INPUT_UNREADABLE`, `INPUT_NOT_REGULAR`, `INPUT_CHANGED_DURING_READ`, `INPUT_TOO_LARGE`, `JSON_INVALID`,
`JSON_ROOT_INVALID`, `SCHEMA_KEYS_INVALID`, `SCHEMA_ID_INVALID`, `STRUCTURE_ID_INVALID`,
`NUMBER_INVALID`, `VECTOR_INVALID`, `MATRIX_INVALID`, `STRUCTURE_KIND_INVALID`, `PBC_INVALID`,
`SITES_INVALID`, `SITE_INVALID`, `SITE_ID_INVALID`, `SITE_ID_DUPLICATE`, `SPECIES_INVALID`,
`ELEMENT_INVALID`, `OCCUPANCY_INVALID`, `OCCUPANCY_SUM_INVALID`.

## Structural semantic blockers

`PERIODICITY_KIND_MISMATCH`, `CELL_SINGULAR`, `ISOLATED_CELL_PRESENT`,
`COORDINATE_REPRESENTATION_MISMATCH`, `ISOLATED_FRACTIONAL_PRESENT`, `SYMMETRY_INVALID`,
`SYMMETRY_STATUS_INVALID`, `SYMMETRY_SCOPE_INVALID`, `SYMMETRY_NUMBER_INVALID`,
`SYMMETRY_SYMBOL_INVALID`, `SYMMETRY_TOLERANCE_INVALID`, `SYMMETRY_EVIDENCE_INVALID`,
`SYMMETRY_PROVENANCE_MISSING`, `SYMMETRY_PROVENANCE_INVALID`, `CHARGE_STATE_INVALID`,
`CHARGE_INVALID`, `SPIN_STATE_INVALID`, `MULTIPLICITY_INVALID`,
`CHARGE_SPIN_PARITY_MISMATCH`, `TOLERANCE_INVALID`.

## Readiness findings inside successful audit output

- `OCCUPANCY_DISORDER_PRESENT`: mixed species share a site; calculation readiness is blocked.
- `PARTIAL_OCCUPANCY_PRESENT`: occupancy sum is below one; calculation readiness is blocked.
- `MOLECULAR_ELECTRONIC_STATE_UNRESOLVED`: charge or multiplicity is unresolved; readiness is blocked.
- `SYMMETRY_DECLARATION_UNVERIFIED`: symmetry is declared but not backend-verified; review is required.
- `SYMMETRY_VERIFICATION_PROVENANCE_UNRESOLVED`: backend/version fields are present, but this
  local audit did not resolve immutable external evidence; review is required.
- `SYMMETRY_UNRESOLVED`: no symmetry claim is made; review is required.
- `PERIODIC_IMAGE_UNWRAPPED`: a coordinate on an axis with `pbc=true` preserves an out-of-cell
  image; nonperiodic slab/wire axes do not trigger this notice.

## Operation and output blockers

`PARAMETER_MISSING`, `SITE_ORDER_INVALID`, `SUPERCELL_PARAMETER_INVALID`,
`SUPERCELL_BUDGET_EXCEEDED`, `OPERATION_SCOPE_INVALID`, `OPERATION_UNSUPPORTED`,
`DERIVED_SITE_ID_INVALID`, `TRANSFORM_INVARIANT_FAILED`, `ROUNDTRIP_LOSSY`,
`OUTPUT_PATH_INVALID`, `OUTPUT_EXISTS`,
`OUTPUT_PARENT_INVALID`, `OUTPUT_PARENT_CHANGED`, `ATOMIC_OUTPUT_UNAVAILABLE`, `OUTPUT_WRITE_FAILED`.

## Provider and internal states

The backend probe reports per-distribution states `match`, `version-mismatch`, or `not-installed`
and returns exit 3 unless all pinned identities match. `UNEXPECTED_INTERNAL_ERROR` returns exit 4
and certifies no result.

All blocked and internal envelopes carry the candidate lifecycle cap. No finding can set
`promotion_authorized` or `execution_authorized` true.
