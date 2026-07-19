# Deterministic workflow

## Evidence flow

Keep the role sequence explicit:

`request -> task profile -> normalized candidate input -> deterministic gates -> optional transform -> round-trip evidence -> export plan -> target DFT skill -> human decision`

The role separation adopts a general multi-agent computational-chemistry design principle: one
component plans, one deterministic component executes bounded operations, one component checks
evidence, and a reviewer retains scientific authority. No file, prose, or implementation from an
external repository is incorporated here.

## Input normalization

Accept raw CIF interpretation only from the active CIF analysis skill. Convert its traceable site
table into `structure-preparation-input` while retaining:

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
| `supercell` | Apply a positive diagonal repeat | One-to-many mapping, replicated IDs, scaled cell, invalidated symmetry |

Compute derived-site count before replication and block above 4096 sites. Wrap only axes whose
PBC flag is true; an integer shift on a nonperiodic axis is a coordinate mutation, not a periodic
image. Bind every emitted mapping list to `site_mapping_sha256`.

The candidate does not implement primitive/conventional standardization, slabs, defects,
adsorbates, bonding, conformers, aromaticity, stereochemistry, or code-format serialization.
Those routes remain blocked until pinned backends and task-specific validation exist.

## Round trip

Interpret classifications as follows:

- `exact`: canonical structure, order, and representation fingerprints all match.
- `equivalent`: sites, species/occupancy, cell, and coordinates match within tolerance after an
  explicit periodic image shift, but representation or order differs.
- `lossy`: at least one required invariant differs or cannot be mapped.
- `not-applicable-derived-structure`: an intentional non-bijective operation such as supercell.

Never call a lossy conversion equivalent because it opens in a viewer or because formulas match.

## Export planning

`plan-export` records the target code, site-to-ordinal mapping, source length unit, unresolved
target unit, requested handoff roles, and non-execution state. It emits no code input, chooses no
code parameter, and reports no generated file. QE, VASP, CP2K, and SIESTA skills must still apply
their own syntax, pseudopotential/basis, numerical, restart, and scientific gates.

For weak-model routing, parse [weak-model-decision-table.json](weak-model-decision-table.json),
select the first matching case in ascending numeric priority, retain `current_claim=no_positive_claim`, and
perform no action stronger than `minimum_next_action`.
