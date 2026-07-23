# Practical provider recipes

Use this reference only after the deterministic candidate audit has established an input
identity and exposed unresolved occupancy, periodicity, coordinate, charge, spin, and mapping
findings. These recipes describe provider calls and acceptance checks; they do not activate a
provider route in this development Skill.

## Contents

- [Evidence labels](#evidence-labels)
- [Record a provider-neutral intake](#record-a-provider-neutral-intake)
- [Use ASE without losing representation](#use-ase-without-losing-representation)
- [Use pymatgen for periodic structures](#use-pymatgen-for-periodic-structures)
- [Use spglib for explicit symmetry evidence](#use-spglib-for-explicit-symmetry-evidence)
- [Use RDKit for molecular starting geometries](#use-rdkit-for-molecular-starting-geometries)
- [Handoff to a DFT calculation Skill](#handoff-to-a-dft-calculation-skill)
- [Accept or reject a prepared output](#accept-or-reject-a-prepared-output)
- [Triage common failures](#triage-common-failures)
- [Apply version-sensitive notes](#apply-version-sensitive-notes)
- [Primary official sources](#primary-official-sources)

## Evidence labels

Interpret labels in this file literally:

- **Official manual fact** means a first-party API page, manual, release, or source repository
  establishes the stated behavior. It is not evidence that the API ran in this repository.
- **Operational heuristic** means a conservative practice distilled from structure-preparation
  work. It is a starting point to validate against the actual material, code, and observable,
  not an official default or scientific acceptance threshold.
- **Candidate boundary** means the current CLI can only audit or plan the operation. A future
  provider adapter still needs a version pin, fixtures, native tests, and promotion review.

Never relabel an operational heuristic as an official recommendation. Never treat a successful
provider call as proof that the resulting physical model is appropriate.

## Record a provider-neutral intake

Before importing a provider, freeze the source and record:

1. Raw-byte SHA-256, byte count, declared format, parser version, and parse options.
2. Structure kind (`periodic` or `molecule`), cell matrix convention, coordinate basis, length
   unit, and per-axis PBC.
3. Ordered species, occupancy, stable site IDs, original order, labels, constraints, and any
   oxidation-state or formal-charge annotations.
4. Total charge, multiplicity or other spin statement, per-site magnetic initialization, and
   whether each value is source data, user decision, or unresolved.
5. Any requested primitive, conventional, wrapping, sorting, merge, replication, defect, or
   molecular-embedding operation as a separate proposed transformation.

Do not silently enable `primitive`, `sort`, atom merging, hydrogen removal, idealization, or
coordinate wrapping while parsing. Each changes either topology, representation, or site
lineage. Preserve the immutable input and write a new result.

For raw CIF syntax, let `cif-structure-analysis` own data-block selection, raw-tag evidence,
standard uncertainties, disorder warnings, and periodic-neighbor interpretation. Normalize only
the selected block into this candidate's JSON schema.

## Use ASE without losing representation

### Read exactly the intended frame

**Official manual fact:** `ase.io.read` returns the last configuration by default, while
`index=':'` returns all configurations. A file-like object requires an explicit `format`.

Use an explicit frame and format whenever ambiguity exists:

```python
from ase.io import read

atoms = read("source.extxyz", index=0, format="extxyz")
```

After reading, inspect `len(atoms)`, `atoms.get_chemical_symbols()`, `atoms.cell.array`,
`atoms.pbc`, `atoms.positions`, `atoms.arrays`, constraints, initial charges, initial magnetic
moments, and attached calculator state. Reject a periodic structure with an undeclared or
singular cell. Reject a molecule that accidentally inherited PBC.

### Change the cell deliberately

**Official manual fact:** `Atoms.set_cell` does not move atoms unless `scale_atoms=True`.
Therefore record which of these distinct operations is intended:

```python
# Change the box while preserving Cartesian positions.
atoms.set_cell(new_cell, scale_atoms=False)

# Apply a homogeneous strain in fractional coordinates.
atoms.set_cell(new_cell, scale_atoms=True)
```

Do not infer strain from a changed cell alone. Preserve the old and new cells, Cartesian and
fractional coordinates, and a statement of which coordinate representation was held fixed.

### Wrap only periodic axes

**Official manual fact:** `Atoms.wrap` honors per-axis PBC. Before mutation, compute and retain
integer image shifts from unwrapped to wrapped fractional coordinates. Recheck that nonperiodic
components did not move.

```python
scaled_before = atoms.get_scaled_positions(wrap=False).copy()
atoms.wrap(eps=1e-7)
scaled_after = atoms.get_scaled_positions(wrap=False)
```

**Operational heuristic:** use wrapping to make a static representation convenient, not to erase
trajectory continuity or adsorbate placement across a boundary. Treat atoms separated only by an
integer periodic image as the same site when constructing the mapping.

### Build a general supercell with lineage

**Official manual fact:** `ase.build.make_supercell(prim, P, ...)` accepts a 3x3 integer
transformation and constructs the cell as `P @ parent_cell`. `order='cell-major'` and
`order='atom-major'` produce different atom orders.

```python
import numpy as np
from ase.build import make_supercell

P = np.array([[2, 0, 0], [0, 2, 0], [0, 0, 1]], dtype=int)
child = make_supercell(parent, P, wrap=True, order="cell-major")
```

Accept only when all of the following hold:

- `abs(det(P))` is a positive integer and both atom count and cell volume scale by it.
- The child cell agrees with `P @ parent_cell` in the same row-vector convention.
- Every child has a unique child ID plus parent site ID and replica/image translation.
- Species, occupancy, constraints, charge/spin policy, and requested atom order are reviewed.

Propagated parent IDs are not unique child IDs. A supercell is derived, not round-trip equivalent.

### Treat calculators as a separate authority

**Official manual fact:** ASE calculators are attached separately to `Atoms`; an `Atoms` object
without a calculator cannot provide energy or forces, and external DFT executables are not part
of ASE itself.

At handoff, separate geometry from calculator configuration. Record the calculator name and
version, parameter dictionary, executable identity, pseudopotential or basis provenance, and
environment independently. Do not serialize cached energy/force results as if they belonged to a
new geometry. After any mutation, require a fresh calculation before reading results.

ASE's conventional base units are angstrom for length, eV for energy, eV/angstrom for force, and
eV/angstrom cubed for stress. Verify the selected calculator's adapter and output convention
rather than assuming a third-party backend uses those units internally.

### Write without silent loss

**Official manual fact:** `ase.io.write` overwrites by default. `append=True` may create an
unreadable file for formats that do not support multiple configurations.

Write only to a new path, re-read with the explicit format, and compare required invariants:

```python
from pathlib import Path
from ase.io import read, write

destination = Path("prepared.extxyz")
if destination.exists():
    raise FileExistsError(destination)
write(destination, atoms, format="extxyz", append=False)
reloaded = read(destination, index=0, format="extxyz")
```

Opening successfully is not enough. Verify atom order, stable IDs, cell, PBC, coordinates,
occupancy representation, constraints, charge/spin fields, and units. Classify the result as
exact, periodic-equivalent, or lossy.

## Use pymatgen for periodic structures

### Parse without hidden topology changes

**Official manual fact:** `Structure.from_file` defaults to `primitive=False`, `sort=False`, and
`merge_tol=0.0`. Keep those values explicit for a representation-preserving read:

```python
from pymatgen.core import Structure

structure = Structure.from_file(
    "source.cif", primitive=False, sort=False, merge_tol=0.0
)
```

Inspect `structure.is_ordered`, lattice, fractional coordinates, site properties, total charge,
and site labels. Do not use `Structure.is_valid()` with its default distance tolerance as a
scientific overlap criterion; choose and record a project-specific short-contact test that
accounts for bonding and periodic images.

### Establish symmetry with an explicit tolerance record

**Official manual fact:** `SpacegroupAnalyzer` uses spglib and defaults to
`symprec=0.01` in lattice-length units and `angle_tolerance=5` degrees. Official pymatgen docs
note that a larger distance tolerance such as 0.1 angstrom may be needed for relaxed structures;
that example is not a universal acceptance value.

```python
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

sga = SpacegroupAnalyzer(structure, symprec=0.01, angle_tolerance=5)
dataset = sga.get_symmetry_dataset()
```

**Operational heuristic:** evaluate a small, declared tolerance ladder around the structure's
numerical precision. Report whether space-group number, Wyckoff assignment, and equivalent-site
groups are stable. Never increase tolerance merely to recover an expected label. Large tolerance
sensitivity is a finding, not permission to choose the preferred result.

### Standardize only with an auditable map

**Official manual fact:** pymatgen's conventional standard structure follows the documented
Setyawan-Curtarolo convention and need not be the International Tables representation.
`get_refined_structure` is the route for an international-setting refinement. Site properties
are not kept by default because, for example, magnetic order may not transfer correctly.

Before accepting a primitive, conventional, or refined structure:

- record `symprec`, `angle_tolerance`, method, provider versions, before/after cells, and symmetry;
- require unchanged composition and a complete parent-site/periodic-image mapping;
- re-evaluate magnetic moments, oxidation states, labels, selective dynamics, and other site
  properties instead of blindly enabling `keep_site_properties=True`;
- reject `None`, ambiguous mappings, or tolerance-dependent topology.

### Build a supercell without mutating the parent

**Official manual fact:** `Structure.make_supercell` accepts scalar, diagonal, or full integer
scaling matrices and mutates in place by default. Prefer an explicit derived copy:

```python
child = structure.make_supercell(P, to_unit_cell=True, in_place=False)
```

Verify determinant, atom-count and volume scaling, cell convention, and full child lineage.
Do not assume total charge scales correctly: make charge and multiplicity a separate post-
transformation decision. Replicated site properties still need unique child IDs.

### Convert through the ASE adaptor conservatively

**Official manual fact:** `AseAtomsAdaptor` supports ASE-to-pymatgen structure and molecule
conversion. Treat the conversion as lossy until revalidated. Compare species/order, cell, PBC,
coordinates, site properties, constraints, initial charge/magnetic arrays, total charge, and
molecular multiplicity. Initial per-atom charge or magnetic moment is not a general total
electronic-state contract.

## Use spglib for explicit symmetry evidence

This is a reference-only cross-check, not an independently registered software/provider route.
It is documentation-backed only in the current candidate, is not exposed by
`structure_prepare.py`, and has no repository-native fixture evidence. Do not use it for routing,
activation, or provider-support claims. Register a future direct adapter before adding such claims.

### Construct the cell tuple correctly

**Official manual fact:** the Python interface accepts `(lattice, positions, numbers)` and an
optional fourth magnetic-moment array. `positions` are fractional coordinates; `numbers` are
integer type identifiers. The identifiers distinguish species but are not oxidation states or
site IDs.

```python
import spglib

cell = (lattice_rows, fractional_positions, integer_species_numbers)
dataset = spglib.get_symmetry_dataset(
    cell, symprec=1e-5, angle_tolerance=-1.0
)
if dataset is None:
    raise ValueError("spglib did not find a symmetry dataset")
```

Record the units of `lattice_rows`; `symprec` uses the same length unit. Record whether magnetic
moments were supplied and whether the magnetic or nonmagnetic API was used.

### Preserve transformation and origin evidence

**Official manual fact:** standardized cells are not unique. `standardize_cell`,
`find_primitive`, and `refine_cell` can return `None`; idealization may rotate or otherwise adjust
the cell. Preserve at least the dataset's transformation matrix, origin shift, equivalent atoms,
mapping to primitive, standardized cell, and standardized-to-primitive mapping.

Use `no_idealize=True` for a mapping-first diagnostic, then run an idealized result separately if
the task needs it. Do not compare standardized coordinates index-by-index without the returned
mapping and periodic image translations.

**Operational heuristic:** run the same declared tolerance ladder used for pymatgen and compare
dataset identity and mappings. If plausible tolerances change the space group, primitive size,
or site grouping, retain the unresolved sensitivity instead of promoting one answer.

### Respect the 2.7 API boundary

**Official manual fact:** spglib 2.7.0 reorganized its Python internals and changed exception
behavior. Import only public top-level APIs, pin the exact version in an adapter, catch documented
exceptions as well as `None` results where applicable, and do not depend on private modules.

## Use RDKit for molecular starting geometries

This route is documentation-backed and `native-not-run` in the current candidate.

### Parse, sanitize, and retain electronic-state evidence

**Official manual fact:** RDKit molecule readers return a `Mol` on success and `None` on failure.
Molfile parsing defaults include sanitization and hydrogen removal; make both policies explicit.

```python
from rdkit import Chem

mol = Chem.MolFromMolFile(
    "source.mol", sanitize=True, removeHs=False, strictParsing=True
)
if mol is None:
    raise ValueError("RDKit parse or sanitization failed")
formal_charge = Chem.GetFormalCharge(mol)
```

Record atom-map numbers, bond orders, aromaticity model, formal charge, radical electrons,
isotopes, stereochemistry, and explicit/implicit hydrogen policy. RDKit formal charge does not
establish a DFT spin multiplicity; preserve an independently justified multiplicity.

### Generate deterministic ETKDGv3 starting conformers

**Official manual fact:** ETKDG has been the default embedding method since 2018.09 and ETKDGv3
the default since 2024.03. Instantiate `ETKDGv3()` explicitly so a future default change cannot
silently alter the recipe.

The variables below are project-supplied campaign choices, not RDKit defaults or universal
recommendations. Select and record them before execution; vary conformer count and optimization
effort when the target observable is sensitive to conformational coverage.

```python
from rdkit.Chem import AllChem

mol_h = Chem.AddHs(mol)
params = AllChem.ETKDGv3()
params.randomSeed = project_seed
params.numThreads = 1
conformer_ids = list(AllChem.EmbedMultipleConfs(
    mol_h, numConfs=requested_conformer_count, params=params
))
if len(conformer_ids) != requested_conformer_count:
    raise ValueError("not all requested conformers embedded")
if not AllChem.MMFFHasAllMoleculeParams(mol_h):
    raise ValueError("MMFF parameters are incomplete")
results = AllChem.MMFFOptimizeMoleculeConfs(
    mol_h, numThreads=1,
    maxIters=optimization_iteration_cap,
    mmffVariant="MMFF94",
)
if any(not_converged != 0 for not_converged, _energy in results):
    raise ValueError("one or more MMFF optimizations did not converge")
```

Record seed, thread count, conformer count, embedding parameter values, conformer IDs, MMFF
variant, iteration limit, status, and energy for each conformer. MMFF methods may change the
molecule's aromaticity flags as part of their own atom typing; revalidate connectivity and
stereochemistry after the call.

**Operational heuristic:** use ETKDG/MMFF to generate diverse initial geometries, not to assert a
DFT conformer ordering. Cluster by geometry, retain more than one chemically plausible seed when
rotors or coordination alternatives matter, and let the target DFT workflow relax and compare
them under a common method.

### Export and reparse each conformer

Write one explicitly selected `confId` to a new path with a declared stereo and V2000/V3000
policy. Reparse it and compare atom order/map numbers, explicit H count, bonds and bond orders,
formal charge, radicals, stereochemistry, and coordinates in angstrom. A successful writer return
without this round-trip is not acceptance.

## Handoff to a DFT calculation Skill

Create a provider-neutral handoff record rather than a nominal input file alone. Include:

- source and prepared-structure hashes; parent/child site and periodic-image mapping;
- ordered species and coordinates, cell, PBC, coordinate basis, and explicit length unit;
- occupancy/disorder decision, total charge, multiplicity/spin state, initial magnetic moments,
  oxidation/formal-charge annotations, and constraints;
- every transformation matrix, origin shift, wrap shift, sort/reorder map, and stochastic seed;
- provider distributions, exact versions, API parameters, warnings, and round-trip result;
- unresolved scientific decisions and the target calculation Skill that must resolve them.

Apply target-specific checks without taking authority from the target Skill:

| Target | Structure handoff checks | Facts not encoded by the structure alone |
|---|---|---|
| QE | Declare `CELL_PARAMETERS` and `ATOMIC_POSITIONS` units/basis; preserve species-label order and cell convention. | Pseudopotentials, cutoffs, k points, occupations, total charge, spin/SOC, and convergence. |
| VASP | Verify scale, lattice-vector convention, species/count order, Direct versus Cartesian coordinates, and selective-dynamics mapping. | POTCAR identity, ENCUT, k points, NELECT/charge, MAGMOM, SOC, dipole handling, and convergence. |
| CP2K | Declare cell, periodic axes, coordinate unit, kind mapping, charge and multiplicity handoff. | Basis/potential provenance, cutoff grids, method, SCF/OT choices, and convergence. |
| SIESTA | Declare lattice and atomic-coordinate formats, species-number mapping, units, charge/spin and constraints. | Pseudopotentials, basis, mesh cutoff, k sampling, electronic method, and convergence. |

Never infer pseudopotential or basis selection from a chemical symbol. Never infer charge or spin
from oxidation-state annotations alone.

## Accept or reject a prepared output

Apply these gates in order. Stop at the first unresolved gate and retain the evidence gathered:

1. **Execution:** the provider returned without exception and wrote the intended new artifact.
2. **Identity:** source and output hashes, versions, API parameters, and parent lineage are present.
3. **Topology:** atom count, species, occupancy, bonds for molecules, and stable site mapping match
   the requested transformation exactly.
4. **Representation:** units, coordinate basis, cell convention, PBC, atom order, constraints,
   charge/spin fields, and custom site properties survived or their loss is explicit.
5. **Geometry:** coordinates are finite, cell is valid, periodic overlap and molecular short-
   contact checks pass, and any wrap/supercell/standardization equation is verified.
6. **Symmetry:** provider/version/tolerances and mapping are recorded; results are not promoted
   beyond their tolerance stability.
7. **Electronic state:** occupancy/disorder, total charge, multiplicity, radicals, magnetic
   initialization, and parity are resolved for the intended calculation.
8. **Target readiness:** the target rigorous-calculation Skill accepts the handoff and independently
   supplies method, potential/basis, sampling, and convergence evidence.

Passing gates 1--7 proves only a traceable prepared input. It does not prove a converged or
physically correct DFT result.

## Triage common failures

| Symptom | Likely cause | Required response |
|---|---|---|
| Correct composition but different atom order | sorting, standardization, supercell order, or format writer | Build an explicit bijection; never compare index-by-index without it. |
| Coordinates differ by lattice vectors | wrapping or periodic image selection | Record integer image shifts and classify periodic equivalence. |
| Space group changes with tolerance | numerical distortion, disorder, magnetism, or wrong cell | Report tolerance sensitivity; inspect structure and provenance before standardizing. |
| Site properties disappear | format cannot represent them or provider default dropped them | Block exact round-trip; carry a sidecar only when the target contract permits it. |
| Charge changes after conversion/supercell | format or provider semantics omit or copy total charge | Require an explicit electronic-state decision and record the new value. |
| RDKit parse returns `None` | invalid valence, kekulization, or strict-format failure | Preserve diagnostics; do not disable sanitization silently. |
| ETKDG returns fewer conformers | embedding failure or incompatible constraints | Keep failure counts and parameters; revise the declared recipe or stop. |
| Provider writer succeeds but target rejects | unit/order/format semantics or missing target fields | Reparse, compare the handoff contract, and let the target Skill own the fix. |

## Apply version-sensitive notes

The following observations were checked against official pages on 2026-07-22. They are not local
execution evidence:

| Provider | Version boundary | Action |
|---|---|---|
| ASE | Repository profile pins 3.29.0; I/O overwrite, frame selection, wrapping, and supercell order are version-sensitive. | Require exact distribution identity and re-run operation fixtures before activation. |
| pymatgen | Wrapper release 2026.5.4 and separate `pymatgen-core` 2026.5.18 are distinct identities; the rolling documentation can show a newer build. | Match API behavior to both pinned distributions; do not use a documentation header as installed identity. |
| spglib | Stable docs/releases expose 2.7.0; Python internals and exception behavior changed in 2.7. | Use public top-level APIs, pin 2.7.0 for a future adapter, and add native `None`/exception/mapping fixtures. |
| RDKit | Official documentation is 2026.03.4; embedding defaults have changed historically. | Instantiate ETKDGv3 and all stochastic settings explicitly; keep this route `native-not-run` until tested. |

## Primary official sources

- ASE Atoms, I/O, supercells, calculators, and units:
  <https://docs.ase-lib.org/ase/atoms.html>,
  <https://docs.ase-lib.org/ase/io/io.html>,
  <https://docs.ase-lib.org/ase/build/tools.html>,
  <https://docs.ase-lib.org/ase/calculators/calculators.html>, and
  <https://docs.ase-lib.org/ase/units.html>.
- pymatgen core, symmetry, I/O, and releases:
  <https://pymatgen.org/pymatgen.core.html>,
  <https://pymatgen.org/pymatgen.symmetry.html>,
  <https://pymatgen.org/pymatgen.io.html>, and
  <https://github.com/materialsproject/pymatgen/releases>.
- spglib Python interface, dataset, definitions, and releases:
  <https://spglib.readthedocs.io/en/stable/python-interface.html>,
  <https://spglib.readthedocs.io/en/stable/dataset.html>,
  <https://spglib.readthedocs.io/en/latest/definition.html>, and
  <https://github.com/spglib/spglib/releases>.
- RDKit Python guide, file I/O, molecule operations, conformer API, and releases:
  <https://www.rdkit.org/docs/GettingStartedInPython.html>,
  <https://www.rdkit.org/docs/source/rdkit.Chem.rdmolfiles.html>,
  <https://www.rdkit.org/docs/source/rdkit.Chem.rdmolops.html>,
  <https://www.rdkit.org/docs/source/rdkit.Chem.AllChem.html>, and
  <https://github.com/rdkit/rdkit/releases>.
