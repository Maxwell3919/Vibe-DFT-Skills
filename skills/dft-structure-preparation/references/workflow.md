# Deterministic workflow

## Evidence flow

Keep the role sequence explicit:

`request -> task profile -> normalized candidate input -> deterministic gates -> optional transform -> round-trip evidence -> export plan -> target DFT skill -> human decision`

The role separation adopts a general multi-agent computational-chemistry design principle: one
component plans, one deterministic component executes bounded operations, one component checks
evidence, and a reviewer retains scientific authority. No file, prose, or implementation from an
external repository is incorporated here.

## Input normalization

Accept raw CIF interpretation only from the active CIF analysis skill. Use `import-cif-manifest`
to validate the public Schema, published identity preimage/hash, cell/coordinate agreement,
ordered sites, and occupancy/disorder boundary before emitting a nested
`structure-preparation-input`. Refuse a blocked, previously transformed, identity-inconsistent,
partially occupied, or disordered manifest rather than silently reducing it to a representative
full-occupancy model. Retain:

- source raw-byte hash outside this candidate envelope;
- stable site identifiers and explicit order;
- every species and occupancy on each site;
- declared periodic dimensions and cell vectors in angstrom;
- fractional and Cartesian coordinates together for periodic systems;
- symmetry status, tolerance, backend, and version without upgrading declarations;
- molecular charge and multiplicity, or an explicit unknown/not-assessed state.

The local envelope is a staging format. It is not a replacement for the repository's active
structure snapshot or molecular structure contracts.

## Audit

Run `audit` first. Treat schema or semantic failures as blockers. A structurally valid record may
still have calculation readiness `blocked` or `requires-decision`. Even a `verified` symmetry
label requires review because the local staging envelope cannot resolve immutable backend evidence.
Require readiness only at the handoff boundary; preserving a disordered structure for inspection
is allowed.

## Transform

Use only these candidate-implemented operations:

| Operation | Deterministic effect | Required evidence |
|---|---|---|
| `wrap` | Wrap periodic fractional components into `[0,1)` | Same site IDs, explicit image shifts, equivalent round-trip |
| `reorder` | Reorder by an exact permutation of site IDs | One-to-one mapping, changed site-order digest, unchanged structural digest |
| `supercell` | Apply a positive-determinant 3x3 integer lattice matrix | One-to-many mapping, lattice cosets, determinant/site-count invariant, invalidated symmetry |
| `strain` | Apply a bounded Cartesian deformation to cell and coordinates | Same fractional sites, deformation matrix and component budget, invalidated symmetry |
| `make-slab` | Repeat and cleave along an input lattice vector aligned with its plane normal | Layer mapping, explicit nonperiodic axis, vacuum and alignment evidence |
| `build-interface` | Search small in-plane repeats and coherently combine two oriented slabs | Both parent identities, repeat/strain/angle/atom budgets, registry shift, gap, cross-interface distance |
| `site-edit` | Insert, remove, or substitute one explicit site | Created/removed/same mapping, composition delta, electronic-state invalidation, distance gate |
| `place-guest` | Place one isolated guest by explicit anchor, position, and XYZ rotation | Two-parent mapping, placement parameters, cell-containment and host-guest distance gates |

Compute determinant and derived-site count before replication and block above 4096 sites. Wrap
only axes whose PBC flag is true; an integer shift on a nonperiodic axis is a coordinate mutation,
not a periodic image. Bind every emitted mapping list to `site_mapping_sha256`.

The native slab route is deliberately narrower than a general surface generator: the selected
lattice vector must already align with the surface normal, and the input origin fixes the
termination. The native interface route consumes two such already oriented slabs, compares small
integer repeats, maps the film onto the selected substrate in-plane cell, and ranks accepted
matches lexicographically by strain, angle mismatch, atom count, and total strain. It does not
choose Miller faces, terminations, polarity corrections, twist angles, reconstructions, or
energetically preferred registries.

Native site insertion and guest placement consume explicit user coordinates. They do not infer
symmetry-unique interstitials, void networks, adsorption sites, molecular conformers, charge
compensation, or stable configurations. Primitive/conventional standardization, arbitrary Miller
slabs, automatic defect/adsorption enumeration, moire construction, bonding, conformer generation,
aromaticity, stereochemistry, and code-format serialization remain blocked until a pinned backend
and task-specific evidence close those routes.

## Round trip

Interpret classifications as follows:

- `exact`: canonical structure, order, and representation fingerprints all match.
- `equivalent`: sites, species/occupancy, cell, and coordinates match within tolerance after an
  explicit periodic image shift, but representation or order differs.
- `lossy`: at least one required invariant differs or cannot be mapped.
- `not-applicable-derived-structure`: an intentional derived operation such as supercell, slab,
  interface, site edit, strain, adsorbate, or host-guest placement.

Never call a lossy conversion equivalent because it opens in a viewer or because formulas match.

## Export planning

`plan-export` records the target code, site-to-ordinal mapping, source length unit, unresolved
target unit, requested handoff roles, and non-execution state. It emits no code input, chooses no
code parameter, and reports no generated file. QE, VASP, CP2K, and SIESTA skills must still apply
their own syntax, pseudopotential/basis, numerical, restart, and scientific gates.

For weak-model routing, parse [weak-model-decision-table.json](weak-model-decision-table.json),
select the first matching case in ascending numeric priority, retain `current_claim=no_positive_claim`, and
perform no action stronger than `minimum_next_action`.
