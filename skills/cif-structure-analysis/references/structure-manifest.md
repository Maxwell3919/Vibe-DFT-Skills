# Structure manifest contract

`contracts/structure-manifest.schema.json` is the canonical interchange contract. `analyze_cif.py` validates every JSON artifact before writing it, and `dftpost validate-manifest structure` can validate an existing artifact.

## Identity and provenance

- `manifest_id` is derived from the source CIF SHA-256 prefix and selected data-block index.
- `source` records only a safe file label, syntax family, byte count, SHA-256, and selected block. It must not contain an absolute path.
- `structure_identity` is an ordered cell-and-site fingerprint. New producer output includes the exact `fingerprint_input`: cell vectors rounded to 10 decimal places, PBC flags, and ordered atomic numbers with wrapped fractional coordinates rounded to 10 decimal places.
- `canonicalization=json-sort-keys-compact-utf8-v1` means serialize that input as UTF-8 JSON with lexicographically sorted object keys, `,` and `:` separators, no insignificant whitespace, JSON booleans, and finite JSON numbers, then take SHA-256. Do not hash the pretty-printed manifest bytes or reconstruct hidden ASE precision.
- The bundle semantic gate also compares the preimage with the published six-decimal `structure.cell.vectors_ang` and ordered `structure.sites` after six-decimal quantization and periodic wrapping. Replacing both the preimage and its hash therefore does not establish consistency.
- The preimage and canonicalization fields are paired but optional for backward schema compatibility. An older record without them passes identity verification only when its v1 hash is reproducible from the published structure payload; otherwise it is `blocked` as unverifiable, never accepted as a positive result.
- The fingerprint is deliberately not invariant to site ordering, origin shifts, basis changes, symmetry standardization, or supercells; read `equivalence_scope` before comparing fingerprints.
- `provenance.command` uses placeholders rather than the local input/output paths. Exact analysis options and dependency versions remain available separately.

## Status

- `PASS`: all recorded checks passed.
- `WARN`: a structure artifact was generated, but at least one declared/detected symmetry conflict, disorder/occupancy limitation, incomplete raw field, short-distance flag, tolerance sensitivity, or other review item exists.
- `BLOCK`: a fail-closed consistency check failed. Do not use numeric claims from a `BLOCK` artifact.

The schema enforces the matching lowercase `validation.status`. Individual checks remain the authoritative reason list.

## Document and materialized structure

`document` preserves data-block inventory and selected-block raw metadata, including original numeric strings and standard uncertainties, atom-site occupancy/disorder fields, symmetry declarations, operations, formulas, and audit fields. `structure` is the ASE-materialized periodic model used for geometry calculations.

These two representations are intentionally separate. Partial occupancy or correlated disorder is not expanded into a statistically complete ensemble. In those cases, formula, mass, density, neighbor, and spglib results describe the representative materialized model and carry warnings.

## Periodic neighbors

Every neighbor edge has `(i, j, shift)`, where `shift` is the integer lattice translation applied to site `j`. The canonical undirected identity treats `(i, j, S)` and `(j, i, -S)` as the same edge while preserving distinct images. Self-image edges are allowed.

`coordination_by_atom` counts directed neighbors in each center's nearest-distance shell. `nearest_neighbor_bond_pairs` is the canonical union of those per-center shells. It is not a bond-order or chemical-bond assignment.

## Symmetry

`symmetry_attempt` records the spglib version, requested `symprec` and angle tolerance, detected dataset, Wyckoff/equivalent-site arrays, transformation/origin data, a tolerance sweep, declared/detected comparison, and standardized primitive/conventional summaries. Standardized summaries are evidence, not replacements for the selected structure.

## Structure-intelligence screening

The v1 contract keeps the following fields optional for backward compatibility. Current `analyze_cif.py` output includes all of them:

- `quality_analysis`: formula/Z comparison when the representative model is comparable, cell numerical quality, short contacts, and occupancy/disorder state;
- `local_geometry`: per-site nearest-shell vectors, distances, angles, and heuristic geometry labels;
- `connectivity_analysis`: periodic graph components and translation ranks across all `topology_scale_factors`;
- `property_screening`: symmetry-only tensor permission screens and structure-only hypotheses;
- `optimization_guidance`: unranked source/primitive/conventional starting points, controls, and blockers.

`provenance.command_options.topology_scale_factors` and the matching execution field bind the graph sensitivity sweep. Older manifests may omit the new option and screening payloads and still validate as `structure-manifest@1.0`; consumers must test for field presence.

These fields deliberately separate input review, geometric classification, property hypotheses, and optimization planning. None records energies, forces, phonons, finite-temperature sampling, convex-hull data, or synthesis evidence. `optimization_guidance.ranking_status` is always `NOT_RANKED`; its safe dotted `coordinates_ref` values point to existing manifest payloads and do not mutate the source or resemble filesystem paths.

## Transformation extension

`transformations` is empty for inspection-only analysis. A future normalizer, supercell builder, slab builder, defect builder, or exporter must append one record per transformation with:

- operation and backend identity/version;
- explicit parameters;
- parent structure fingerprint;
- output-to-parent site mapping, using `null` only for a newly created site.

A transformation that changes the structure must produce a new structure fingerprint and must not overwrite the source manifest in place. Changing required fields, identity semantics, or acceptance meaning requires a new contract major version.
