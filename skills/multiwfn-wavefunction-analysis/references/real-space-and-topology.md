# Real-space functions, grids, weak interactions, and topology

This reference summarizes Multiwfn manual sections 2.6, 3.1-3.5, 3.14, 3.17,
3.20, and relevant version-history notes. **Manual fact** marks a pinned manual
or official update-history statement. **Operational heuristic** marks a
practitioner check added by this repository; validate it for the actual system
before relying on it.

## Contents

1. Define the scalar field
2. Choose dimensional and grid routes
3. Process and converge grids
4. NCI and IGM-family descriptors
5. QTAIM critical points and paths
6. Basin integration and closure
7. Failure diagnosis

## Define the scalar field before drawing it

Record the exact field, mathematical convention, source, and unit. Multiwfn
normally reports atomic units unless the prompt or exported format states
otherwise.

| Field | Required distinction | Interpretation boundary |
|---|---|---|
| Electron density `rho` | all-electron, valence-only, or EDF-augmented; total or spin channel | density alone does not partition atoms or prove a bond |
| Density gradient | vector norm versus components | small gradient is not automatically a critical point |
| Laplacian | Multiwfn uses `nabla^2 rho` | some AIM programs display `-1/4 nabla^2 rho`; compare conventions before signs |
| Kinetic-energy density | positive-definite `G`, Laplacian-related `K`, or another definition | kinetic-energy density is not unique |
| Spin density | alpha minus beta under the loaded convention | preserve sign, unrestricted/restricted convention, and expected integrated spin |
| ELF/LOL | exact formula and orbital/electron treatment | high ELF can describe cores, lone pairs, or covalent regions; it is not a single bonding label |
| RDG/NCI field | actual-wavefunction versus promolecular density | promolecular and wavefunction routes are different models |
| `sign(lambda2)rho` | Hessian eigenvalue ordering and density convention | color ranges/isovalues are visualization parameters, not interaction energies |
| IGM/IGMH/mIGM/amIGM | exact variant, program version, fragment definition | similarly shaped surfaces from different variants are not numerically interchangeable |

**Manual fact:** nonlinear functions generally cannot be reconstructed by
summing independently evaluated orbital contributions. Do not claim orbital
decomposition of a nonlinear field unless the manual defines that exact route.

## Choose the dimensional route deliberately

| Main function | Dimensional task | Minimum evidence |
|---:|---|---|
| 1 | value, gradient, and Hessian at a point | point coordinates and units; exact field; source identity |
| 3 | property along a line | endpoint definition, sampling, path coordinate, unit, interpolation |
| 4 | property in a plane | origin/three-point or atom-defined plane, bounds, spacing, field, color scale |
| 5 | property in a spatial region | explicit box/cell, spacing or point counts, field, output format |
| 13 | grid-data processing | grid identities, compatible geometry, operation, output metadata |

The manual's low/medium/high grid presets correspond to approximate total
point counts rather than a universal physical spacing. They therefore become
coarser as the box grows.

**Operational heuristic:** for a quantitative integral, basin property, or
surface-dependent value, use explicit box margins and spacing. Repeat with a
larger box and finer spacing until the reported quantity changes less than a
predeclared tolerance. A visually unchanged image is not convergence.

For every 3D grid, preserve:

- origin, three axis vectors, counts, coordinate and value units;
- molecular versus periodic cell and whether endpoints are duplicated;
- selected field and total/spin/orbital channel;
- box construction and extension beyond the outermost atoms;
- minimum, maximum, integral, nonfinite count, and expected conservation law;
- fixed-name output handling and SHA-256.

Reject a cube when it is empty, unchanged from a pre-existing file, contains
nonfinite values, truncates relevant density at the boundary, or has metadata
incompatible with the downstream tool.

## Process grids without losing their meaning

Main function 13 can transform, combine, integrate, translate, and duplicate
grids. Before arithmetic between two grids, require identical origin, axis
vectors, and point counts. If resampling is necessary, document the
interpolation method and validate an integral or another invariant before and
after resampling.

**Manual fact:** the current version includes a periodic grid-duplication route
and the official update history records a `2026.7.15` fix for a periodic
free-volume grid bug. Record the exact banner/update date whenever results
depend on that operation.

For subtraction or deformation density:

1. show that all component grids use the same geometry, cell, electron/core
   convention, method, and numerical grid;
2. state the subtraction formula and sign;
3. preserve each component and the result;
4. integrate the result and compare with the expected electron difference;
5. do not interpret local lobes until global alignment and conservation pass.

The manual may invoke Gaussian automatically to generate atomic wavefunctions
for promolecular or deformation-density routes. Treat that as a separate
external execution requiring explicit authorization, executable/version
identity, atomic-state choices, and output provenance. Sphericalizing atomic
densities is a modeling decision, not a unique reference construction.

## Use weak-interaction methods as descriptors, not energies

### NCI and RDG

- State whether density and derivatives come from the actual wavefunction or a
  promolecular approximation.
- Record RDG cutoff, density cutoff, `sign(lambda2)rho` range, grid box and
  spacing, and every visualization isovalue/color range.
- Check box/spacing convergence and sensitivity to the displayed isovalue.
- Do not convert surface color or volume into an interaction energy unless a
  separately validated method defines that mapping.

### IGM, IGMH, mIGM, and amIGM

- IGMH requires wavefunction information and an explicit atom/fragment
  partition. Geometry-only mIGM is a different approximation.
- Record fragment atom ranges explicitly and verify them against the loaded
  atom order. Tutorial ranges such as `1-12` and `13-25` are never defaults.
- Record the exact variant and program date. **Manual/version-history fact:**
  the IGM/IGMH formulation changed in 2021, so older and newer numerical
  results can differ. The update history later introduced mIGM/amIGM and
  recommends amIGM over older aNCI/aIGM routes for the use cases it covers.
- Preserve the numerical grids such as `dg_inter.cub` and `sl2r.cub`, not only
  a rendered surface.
- Test fragment-definition sensitivity when the scientific claim depends on
  assigning an interaction to fragments.

**Operational heuristic:** use a weak-interaction surface to locate and compare
regions under a fixed protocol. Do not use its mere existence to assert
stability, bond type, causality, or energetic importance.

## Build a QTAIM/topology workflow

### Know the critical-point types

For a three-dimensional scalar field, the manual uses:

| Rank/signature | Common density-topology name | Local character |
|---|---|---|
| `(3,-3)` | nuclear critical point (NCP) | local maximum |
| `(3,-1)` | bond critical point (BCP) | saddle point with two negative curvatures |
| `(3,+1)` | ring critical point (RCP) | saddle point with one negative curvature |
| `(3,+3)` | cage critical point (CCP) | local minimum |

For an isolated system, check the Poincare-Hopf relation
`NCP - BCP + RCP - CCP = 1`. For a fully periodic cell, the corresponding
relation is `0` under the manual's periodic convention.

A failed relation demonstrates an incomplete/inconsistent topology search. A
passing relation is necessary but not sufficient: duplicate points, missed
symmetry-equivalent points, poor paths, or an inappropriate field can remain.

### Plan searches in layers

1. Search NCPs from nuclear positions.
2. Search likely BCPs from atom-pair midpoints under a stated pair cutoff.
3. Search RCPs from suitable atom triangles and CCPs from polyhedral/pyramidal
   starting regions when the structure warrants them.
4. Add random, spherical, or user-defined starts for complex fields and
   non-obvious noncovalent regions.
5. Deduplicate candidates with a stated distance tolerance.
6. Refine each point and calculate the gradient norm and Hessian eigenvalues.
7. Generate paths only after the critical point has converged.
8. Repeat with stricter numerical/search settings and additional starts until
   the inventory and target properties are stable.

Record the search algorithm, starting-point construction, atom-pair cutoff,
random seed/count if used, step scale, trust radius, maximum iterations,
gradient convergence threshold, duplicate-distance threshold, and path
integration settings. The documented GUI prefix in `calling-and-recipes.md` is
not an unattended search recipe; capture every GUI choice or use a fully
verified text route before automation.

### Audit each critical point

For every retained point, export or record:

- field name and electron/core convention;
- coordinates and coordinate unit;
- rank/signature and all three Hessian eigenvalues;
- gradient norm and convergence status;
- density and any additional requested descriptors with units/conventions;
- connected nuclei or path endpoints and path length;
- search source and duplicate-resolution decision;
- program/banner/settings/source hashes.

**Operational heuristic:** perform a small displacement check around a
critical point when eigenvalues are nearly zero or the rank/signature is
numerically unstable. Refine the grid/wavefunction/search before assigning a
topological type.

### Limit the chemical claim

A BCP or bond path is a topological feature of the selected scalar field. Its
presence alone does not prove a conventional chemical bond, energetic
stabilization, charge transfer, or a specific bond order. Correlations involving
`rho` or the Laplacian at a BCP are method-, system-family-, and convention-
dependent. Establish applicability with comparable reference systems and
uncertainty/sensitivity checks.

For ECP calculations, report whether core density is absent, represented by
EDF, or reconstructed another way. Do not compare all-electron and valence-only
NCP/basin inventories without an explicit compatibility argument.

## Basin integration and closure

When main function 17 or another route integrates atomic basins:

- preserve the field, basin definition, integration grid/algorithm, radial and
  angular settings, and treatment of unassigned boundary points;
- check the sum of basin electron populations against the whole-system
  electron count and the sum of basin volumes/properties against the
  corresponding global integral where applicable;
- report the residual and predeclare an acceptable numerical tolerance;
- refine both search topology and basin integration; refining only one cannot
  repair errors in the other;
- distinguish numerical closure from physical uniqueness of the partition.

Do not accept basin charges or delocalization indices merely because the table
was printed. Require atom-order identity, finite values, global closure, and
stability under reasonable numerical refinement.

## Failure diagnosis

| Symptom | Likely causes to test | Required response |
|---|---|---|
| Electron-density integral is low | grid box truncation, coarse spacing, missing EDF, wrong source | enlarge/refine; inspect ECP/EDF; compare source electron convention |
| Laplacian signs disagree with another code | `nabla^2 rho` versus `-1/4 nabla^2 rho`, units, field mismatch | convert conventions explicitly; compare at identical coordinates |
| Poincare-Hopf fails | missed CPs, duplicate handling, poor starts, periodic convention mismatch | broaden searches; tighten convergence; inspect duplicates and cell semantics |
| CP type changes on refinement | near-degenerate Hessian, insufficient precision, wrong field/source | report unstable; refine source/search; do not assign a definitive type |
| Surface disappears when box/grid changes | discretization or display-isovalue dependence | report sensitivity; establish grid and visualization robustness |
| IGMH fragments look wrong | atom-order/range error, periodic images, wrong variant | verify atom map and PBC; rerun only after exact fragment definition |
| Grid arithmetic produces artifacts | misaligned origin/vectors/counts, unit/channel mismatch | reject direct arithmetic; align with a validated resampling protocol |
| Fixed cube appears despite run failure | stale output from a previous run | require fresh scratch and pre-run absence; compare mtime/hash and transcript |

Technical completion means the intended field/path/grid was produced under the
recorded protocol. Scientific acceptance additionally requires source quality,
numerical convergence, method applicability, and an interpretation no stronger
than the descriptor supports.
