# Pipeline workflow

## Role sequence

Keep the evidence flow explicit:

`request -> trajectory inventory -> pipeline specification -> deterministic plan -> explicit authorization -> exact provider execution -> artifact validation -> expert review`

This architecture follows a general computational-agent principle: use specialized roles for
planning, bounded execution, evidence checking, and scientific judgment. No file, wording, or code
from an external computational-chemistry repository is included.

## Inventory

The candidate parser supports standard XYZ and the extxyz fields needed for deterministic fixture
gates: `Lattice`, `pbc`, `Properties`, species, positions, scalar integer `id:I:1`, and additional
columns described by `Properties`. It records per-frame hashes, atom counts, species order,
particle identifiers, cell vectors/PBC, and available property names and typed schemas. Every
declared `R`, `I`, `L`, or `S` value is checked.
Plain XYZ atom records must contain exactly a species token and three coordinates; unlabeled extra
columns are refused and must instead be declared through extxyz `Properties`.
Cross-frame atom-count, species-order, property-schema, PBC, and cell-presence drift blocks
analysis readiness; a changing but present cell is explicit `cell_mode=variable` and requires a
policy decision.

Stable unique `id:I:1` values preserve mapping if storage order changes; duplicates, changing ID
sets, or a species/ID mismatch fail closed. Otherwise mapping remains ordinal-only. The parser
does not assign identifiers. XYZ/extxyz has no physical-unit declaration in this contract, so all
lengths remain `undeclared-source-native` until the pipeline supplies an explicit unit.

It deliberately does not parse LAMMPS dump, GSD, NetCDF, HDF5, VASP trajectories, bond topology,
or arbitrary OVITO-supported formats.

## Plan

The local pipeline schema requires:

- exact source SHA-256 and format from the inventory;
- provider profile `ovito-basic` or `ovito-pro` and exact version `3.15.5`;
- bounded unique frame indices or an explicit half-open range;
- ordered operations with unique IDs, exact parameter keys, and evidence roles;
- output IDs, artifact kinds, and basename-only labels;
- periodic and atom-mapping policies;
- explicit source length unit (`undeclared`, `angstrom`, `nanometer`, or `bohr`); numerical
  cutoff parameters are blocked while it is undeclared;
- the fixed `technical-only` claim boundary.

`plan` does not import OVITO. It returns exit zero when planning completed even if
`execution_readiness=blocked`; request strict readiness when execution is the next step. The plan
emits `authorization_scope_sha256` over source hash, inventory-record hash, pipeline-spec hash,
provider, selected frames, and operation identities. It remains `planned-not-executed` and cannot
authorize itself.

## Operation catalog

| Operation | Minimum profile | Candidate execution | Evidence role |
|---|---|---|---|
| `compute-frame-metadata` | Basic | implemented | technical-metadata |
| `coordination-analysis` | Basic | plan-only | numerical-analysis |
| `common-neighbor-analysis` | Basic | plan-only | numerical-analysis |
| `atomic-strain` | Pro | plan-only | numerical-analysis |
| `dislocation-analysis` | Pro | plan-only | numerical-analysis |
| `render-image` | Pro in this conservative profile | plan-only | visual-only |
| `export-table` | Basic | plan-only | technical-export |

The profile is intentionally conservative. Reclassify an edition boundary only after checking
the exact official 3.15.5 documentation and adding an edition-specific integration test.

## Execute

`execute` requires the explicit authorization flag, the exact plan scope hash, a new durable
output path, a ready Basic plan, exact source hash, matching `ovito==3.15.5` distribution metadata,
exact imported module version, and only implemented operations. After a single bounded safe read,
it imports the already verified bytes through a private snapshot using
`ovito.io.import_file(snapshot, sort_particles=False)` rather than reopening the user
path. Before any provider import, it deterministically reparses that snapshot and requires the
parser-derived inventory evidence to match the supplied inventory record. It preflights output
before provider import and atomically publishes only a complete result.
The result records particle count, property names, SimulationCell vectors, PBC, particle
identifiers when inventoried, and source-order policy. It refuses the result if computed particle
count/cell/PBC/identifier evidence disagrees with the selected inventory frame.

The executor does not render, modify the pipeline, export data, or run numerical modifiers. It
never executes Pro. Any import/API/compute exception becomes one blocked finding without a partial
certification.

For weak-model routing, parse [weak-model-decision-table.json](weak-model-decision-table.json),
select the first matching case in ascending numeric priority, retain `current_claim=no_positive_claim`, and
perform no action stronger than `minimum_next_action`.
