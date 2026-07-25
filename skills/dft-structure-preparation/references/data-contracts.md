# Candidate and shared-contract boundary

## Candidate-local schemas

`schemas/structure-preparation-input.schema.json` describes the normalized staging input.
`schemas/structure-preparation-output.schema.json` describes the common CLI output envelope.
It also covers the dedicated `structure-preparation-error` envelope emitted on stderr, so blocked
and internal-error exits retain the same lifecycle and provenance fields as normal reports.
The Python CLI also enforces cross-field semantic obligations that JSON Schema alone does not
prove, including unique IDs, occupancy sums, determinant, coordinate residual, charge/spin
parity, mapping coverage, and periodic image shifts.

`import-cif-manifest` first validates the shared `structure-manifest@1.0` Schema, then checks its
canonical identity preimage/hash against the published cell and ordered sites. It refuses
`BLOCK`, existing transformation lineage, partial occupancy, and disorder because the staging
schema cannot carry those upstream meanings without loss. Its `structure-preparation-import`
envelope contains the normalized record under `child`; it is an adapter result, not a new shared
snapshot or a re-parse of source CIF bytes.

These schema IDs contain `candidate`. They must not be registered as production interfaces.
The canonical `references/weak-model-decision-table.json` is a projection of shared
`candidate-decision-table@1.0`: first match by priorities `1..N`, with a final evidence-free
fail-closed default. It is routing guidance and never an activation record.

## Shared contract adaptation

An eventual activation adapter must map without information loss:

| Candidate evidence | Shared destination |
|---|---|
| normalized cell, PBC, ordered sites, charge/spin, identity | `structure-snapshot@1.0` |
| molecular charge, multiplicity, connectivity boundary | `molecular-structure-manifest@1.0` |
| parent/child identities, operation, parameters, mapping, image shifts, round trip | `structure-transformation-manifest@1.0` |
| target, atom order, units, generated files and parser round trip | `structure-export-manifest@1.0` |

The candidate CLI does not emit these shared records because it cannot resolve repository bundle
record references, raw-byte record hashes, topological order, external validation summaries, or
activation-time producer identity in isolation.

## Identity semantics

The candidate emits independently reviewable SHA-256 identity domains:

- `structure_sha256`: periodicity, labeled sites, composition/occupancy, geometry, charge, and spin;
- `geometry_sha256`: unlabeled canonical positions, wrapping only axes marked periodic;
- `labeled_structure_sha256`: site labels bound to species, occupancy, and canonical positions;
- `site_order_sha256`: exact ordered site-ID sequence;
- `periodicity_sha256`: structure kind and PBC state;
- `composition_occupancy_sha256`: site species and occupancies;
- `electronic_state_sha256`: charge and spin state;
- `symmetry_sha256`: exact symmetry representation and provenance fields;
- `representation_sha256`: raw ordered coordinates and representation state.

All digests use sorted-key, compact UTF-8 JSON, finite numbers, and 12-digit coordinate
normalization for the canonical structural payload. They are candidate evidence, not a declared
universal structure identity standard.

No single domain hash may upgrade `lossy` to `equivalent`. Exact requires every domain and
representation to match. Equivalence permits only bounded cell/coordinate residuals, exact
scientific-state domains, reordering, and integer image shifts on axes periodic in both records.

## Atom mapping semantics

Every mapping names parent and child site IDs, plus a parent role for multi-parent operations.
Periodic equivalence uses
`child_to_parent_image_shift`, the integer vector added to the child fractional coordinate to
reconstruct the parent image. Supercell mapping uses `replicated` relations, records the source
site's `parent_image_shift_to_canonical` separately from each `replica_shift`, and remains
non-bijective. General integer matrices additionally record a deterministic lattice-coset
representative. Explicit site edits use null parent or child endpoints with `created` or `removed`;
multi-parent interface and guest operations qualify each source endpoint with `parent_role`.
Unexplained missing, ambiguous, created, or removed endpoints still block.

Every mapping list is bound by `site_mapping_sha256`. Every supercell or combined interface is
capped at 4096 derived sites before materialization and is classified as derived, never exact or
equivalent. Candidate `operation=merge` plus `operation_family=interface` adapts to the shared
`merge` operation class; `slab`, `interstitial`, `substitution`, `remove-sites`, and `adsorbate`
map directly to shared operation classes. Candidate-local operation profiles are not registered
production profiles until promotion.

## Lifecycle envelope

All current outputs set `claim_ceiling=no_positive_claim`, `promotion_authorized=false`, and
`execution_authorized=false`. `future_gate_ceiling` preserves a potential post-promotion gate
class without upgrading the candidate. Export plans additionally set
`target_write_performed=false`, `target_parameter_selection_performed=false`, and
`generated_target_files=[]`.
