# VASPKIT practical workflow and acceptance playbook

## Contents

1. [Evidence labels](#evidence-labels)
2. [Shared parent-run gate](#shared-parent-run-gate)
3. [Input and structure preparation](#input-and-structure-preparation)
4. [Bands, DOS, and PDOS](#bands-dos-and-pdos)
5. [Fermi-surface workflow](#fermi-surface-workflow)
6. [Work-function workflow](#work-function-workflow)
7. [Optical and transition-dipole workflows](#optical-and-transition-dipole-workflows)
8. [Molecular-dynamics workflows](#molecular-dynamics-workflows)
9. [Operational heuristics](#operational-heuristics)
10. [Failure triage](#failure-triage)

## Evidence labels

Keep every statement in this playbook in one of four layers:

- **official tutorial fact**: the VASPKIT 1.5 tutorial shows the task, prompt,
  input, or output;
- **official catalog fact**: the 1.5 feature page lists the task name but does
  not establish its prompt or file schema;
- **operational heuristic**: a conservative practice derived from routine
  VASP/VASPKIT use; it is not a VASPKIT default or universal threshold;
- **native evidence**: a captured exact-version run with executable identity,
  stdin/argv, source hashes, transcript, and output hashes.

Do not turn a catalog fact or heuristic into a runnable prompt. When the exact
installed menu differs from the web pages, the installed version controls the
run and the disagreement remains part of the record.

## Shared parent-run gate

Before postprocessing, bind all required files to one accepted VASP lineage.
At minimum record:

- VASP version/build, task purpose, structure hash, INCAR settings hash,
  KPOINTS hash, and privacy-safe potential identity;
- electronic and ionic completion separately, plus observable-specific
  convergence in cutoff, k sampling, bands, smearing, cell/vacuum, or MD
  length as applicable;
- collinear/noncollinear/SOC state, occupation scheme, spin channel
  convention, and whether symmetry was enabled;
- the energy reference actually used by VASPKIT, including
  `SET_FERMI_ENERGY_ZERO` and any `FERMI_ENERGY.in` override;
- every source file's pre-run SHA-256 and whether the file was produced by a
  restart, static continuation, line-mode run, dense-mesh run, or MD segment.

Reject mixed directories in which, for example, `DOSCAR` belongs to a dense
DOS run but `EIGENVAL` belongs to an older band run. A parseable file set is not
proof of a coherent parent.

## Input and structure preparation

The official 1.5 documentation establishes the following task purposes. Use
the exact-version menu interactively unless a prompt is already pinned in
[calling-and-recipes.md](calling-and-recipes.md).

| Task | Official purpose | Practical acceptance gate |
|---:|---|---|
| 101 | Customize `INCAR` from task tokens | Treat the file as a starting template. Diff every active tag against the scientific plan and validate it with `vasp-rigorous-calculations`. |
| 102 | Generate SCF `KPOINTS` from `POSCAR` | Check mesh, centering, dimensionality, symmetry compatibility, and observable-specific convergence. |
| 103 | Generate `POTCAR` with configured defaults | Verify functional, ordered potential labels, element order, and license boundary without reading or recording potential contents. |
| 104 | Generate `POTCAR` with user-selected potentials | Apply the same checks as 103 and retain the selector transcript. A menu recommendation is not scientific validation. |
| 105 | Convert CIF to `POSCAR` without fractional occupations | Stop on disorder, mixed/partial occupancy, unresolved symmetry, or ambiguous species; preserve the CIF identity and conversion report. |
| 106 | Convert Materials Studio XSD to `POSCAR` while retaining fixes | Verify coordinate convention, cell, element order, and all selective-dynamics flags. |
| 107 | Reformat `POSCAR` in a specified element order | Recompute the site mapping and ensure selective dynamics, velocities, labels, and every companion file are remapped consistently. |
| 108 | Generate/check a VASP input bundle successively | Audit each component independently; chained generation is not an acceptance gate. |
| 109 | Conflicting official labels | Stop. The feature page says job submission while the tutorial says input checking. Inspect the exact binary menu and never automate from the number alone. |

The task-101 tutorial explicitly warns that generated parameters need manual
adjustment and shows that existing `INCAR` handling depends on
`SET_INCAR_WRITE_MODE`. Therefore:

1. copy an existing input set to scratch;
2. record whether the target file exists;
3. capture the active write mode;
4. run the generator only after deciding whether override, append, or backup
   semantics are safe;
5. diff the result before any VASP submission.

Never commit a generated `POTCAR`, its bytes, or private library paths. A hash
or approved privacy-safe potential label may be retained in the run manifest.

## Bands, DOS, and PDOS

Use the detailed prompts in [calling-and-recipes.md](calling-and-recipes.md).
The following matrix is the minimum acceptance layer.

| Goal | VASPKIT route | Required parent evidence | Reject when |
|---|---|---|---|
| Conventional bands | 301–303, accepted VASP line path, then 211 | checked primitive-cell/site map, explicit path convention, matching `INCAR`, `DOSCAR`, `EIGENVAL`, `POSCAR`, `KPOINTS` | path labels are missing, the Fermi reference is detached, or extrema are not sampled/converged |
| Projected bands | 212–216 | conventional-band evidence plus matching projection-bearing `PROCAR`, `LORBIT`, atom/orbital map, spin/SOC semantics | projection totals/labels are inconsistent or selectors were not retained |
| Hybrid bands | 251, accepted hybrid VASP run, then 252–257 | weighted SCF mesh plus zero-weight path, retained `KPATH.in`, enough bands, projection data for 253–257 | the path was treated as an ordinary SCF mesh or prompt sequences were inferred across task families |
| TDOS | 111 | accepted DOS parent, energy grid, occupation method, Fermi convention, normalization | smooth plotting is the only check or electron-count semantics are unknown |
| PDOS | 112–115 | TDOS evidence plus `LORBIT`, exact atom/element/orbital selectors, spin columns | channels are silently summed or orbital labels are inferred from column position alone |

For semiconductors, distinguish the sampled band gap from the global gap. For
metals and small-gap systems, test sensitivity to k sampling, occupation
method, and the energy-zero convention. Projected weights describe the PAW
projection used by the parent; they are not unique atomic charges, bond orders,
or oxidation states.

## Fermi-surface workflow

### Official tutorial route

The VASPKIT 1.5 tutorial establishes this bulk example chain:

1. place an optimized **primitive-cell** `POSCAR` in a scratch directory;
2. run task `261`, provide a reciprocal-space resolution in units of
   `2*pi/angstrom`, and retain the generated `KPOINTS`;
3. run and accept the corresponding VASP electronic calculation;
4. run task `262` on matching `INCAR`, `POSCAR`, `DOSCAR`, and `EIGENVAL`;
5. validate the new `FERMISURFACE.bxsf` before visualization in XCrySDen.

The tutorial's `0.008` resolution is an example, not a convergence result. It
also describes generation of potential input in the prose, but the shown task
261 transcript only establishes a newly written `KPOINTS`; discover and audit
any extra file from the exact binary rather than assuming it.

### Related catalog-only tasks

| Task | Feature-page label | Automation state |
|---:|---|---|
| 263 | Fermi surface in FermiSurfer format | interactive discovery required |
| 264 | projected Fermi surface in FermiSurfer format | interactive discovery required; projection parent required |
| 265 | summed projected Fermi surface for selected atoms/orbitals | interactive discovery required; retain every selector |
| 266 | Fermi surface for 2D materials | interactive discovery required; prove 2D reciprocal convention |
| 267 | projected Fermi surface for 2D materials | interactive discovery required; projection and 2D gates both apply |

Do not guess output filenames for 263–267 from the format names.

### Acceptance gates

- prove that the cell used for task 261 is the intended primitive cell and
  preserve any conventional-to-primitive atom mapping;
- converge the topology and relevant extremal dimensions of each sheet with
  respect to the dense mesh, not merely the total energy;
- preserve the exact Fermi level source and test whether small plausible
  shifts alter pockets or connectivity;
- identify every spin channel and SOC/noncollinear convention; never call a
  band index globally meaningful without the corresponding k/spin mapping;
- confirm reciprocal coordinates, units, symmetry expansion, band count, and
  which bands cross the chosen energy;
- compare a small set of symmetry points or a representative slice against
  the parent eigenvalues before trusting an interpolated surface;
- record viewer settings separately. Selecting one visually attractive band
  or isovalue is not a scientific acceptance criterion.

## Work-function workflow

Use task `426` for the documented planar-average route and task `427` only
after its exact averaging dialogue is captured. Require `LOCPOT` and the Fermi
level from the same accepted slab calculation. Record whether `LOCPOT` was
written from total local potential or ionic-plus-Hartree electrostatic
potential, because the official tutorial discusses both and illustrates a
work-function route using `LVHAR`.

Accept a work function only after:

- the surface normal and averaging direction agree;
- the vacuum region has a numerically flat plateau and is converged with
  vacuum thickness;
- both sides of an asymmetric slab are handled explicitly;
- dipole correction, slab charge, and electrostatic boundary conditions are
  recorded;
- the plateau and Fermi level share the same energy reference;
- the reported value includes the plateau-selection uncertainty or
  sensitivity.

Task success only establishes an averaged potential table, not a converged
surface work function.

## Optical and transition-dipole workflows

### Version-sensitive task map

The official pages disagree. The feature page labels `710` as 2D linear
spectra, `711` as bulk linear spectra, and `713` as a transition-dipole route.
The tutorial menu instead shows `711` for linear spectra, `712` for a single
k-point TDM, and `713` for a band-path TDM. Treat `710–713` as one conflict
set and capture the exact installed menu before creating stdin.

### Tutorial-grounded task 711 route

For the tutorial's bulk route, task `711` asks for an output energy unit
(`eV`, `nm`, or `THz`). When both `REAL.in` and `IMAG.in` are absent, the
tutorial states that VASPKIT 1.00+ reads the dielectric function from
`vasprun.xml`. It derives linear spectra such as refractive index, extinction
coefficient, absorption coefficient, energy-loss function, and reflectivity.
The tutorial explicitly says this module is not suitable for low-dimensional
materials.

Validate the parent optical calculation rather than copying the public example
settings. Check at least k-point density, occupied and unoccupied bands,
frequency grid, broadening, tensor directions, polarization averaging,
intraband treatment for metals, and whether the requested physics needs local
fields, excitons, electron-hole interactions, or a dimensional normalization
outside this independent-particle conversion.

### Tutorial-grounded TDM routes

- the shown task `712` accepts one k-point index and two band indices, reads
  `WAVECAR`, and reports squared TDM components in `Debye^2`;
- the shown task `713` accepts a conventional/hybrid band mode plus two band
  indices and writes `TDM.dat` after reading `WAVECAR` and a compatible
  `KPOINTS` path;
- the tutorial requires `LWAVE=.TRUE.`, says its shown implementation supports
  the standard VASP binary, and warns that the band-path route expects
  VASPKIT-created hybrid-band KPOINTS.

Confirm these prompts against the installed binary. Reject a TDM claim when
band ordering changes along the path, degenerate/subspace states are treated
as uniquely labeled scalar bands, gauge/phase and polarization conventions are
unknown, the `WAVECAR` does not match the structure/k points, or only the
magnitude plot is retained without the source indices and units.

## Molecular-dynamics workflows

### Official task map and conflict

| Task | Official feature-page purpose | Public recipe state |
|---:|---|---|
| 721 | mean-squared displacement | tutorial shows `POSCAR.ref`, `MSD.dat`, and `ATOM_DISPLACEMENT.dat` |
| 722 | FFT mean-squared displacement | **documentation conflict**: the tutorial prose calls 722 an RDF task; exact-binary inspection required |
| 723 | diffusion coefficient and ion mobility from `MSD.dat` | catalog-only |
| 725 | pair-correlation function from `PCDAT` | catalog-only |
| 726 | radial distribution function for selected elements | catalog-only |
| 727 | velocity autocorrelation function | catalog-only |
| 728 | vibrational DOS from velocity autocorrelation | catalog-only |
| 730 | bond-length distribution for selected elements | catalog-only |
| 731 | bond-angle distribution for selected elements | catalog-only |
| 736 | selected-atom trajectory in POSCAR format | catalog-only |
| 737 | selected-atom trajectory in PDB format | catalog-only |

Only task 721 has a usable public output recipe in the pinned tutorial. Do not
invent prompts or output names for the remaining tasks.

### MD parent gate

Bind the trajectory to one MD protocol and retain:

- initial/reference structure, ensemble, thermostat/barostat, target
  temperature/pressure, electronic settings, timestep, output stride, and all
  restart segments;
- species/site mapping across segments, cell vectors at every sampled step
  when the cell changes, and the exact source used by VASPKIT;
- total simulated time, equilibration discard, production interval, sampling
  interval, and whether positions were wrapped;
- energy/temperature/pressure traces and evidence that the trajectory is
  stable enough for the requested observable.

The official Nature Protocols companion repository contains an MD input
example, but example values and even example-file syntax must be reviewed
before use. An example is not a transferable ensemble or convergence recipe.

### Observable acceptance

- **MSD:** verify periodic unwrapping, atom/species selection, reference/origin
  definition, directional versus total convention, and consistency between
  time step and row index. Inspect multiple time origins where appropriate.
- **Diffusion/mobility:** predeclare a diffusive fit window, dimensionality, and
  Einstein-relation convention. Require a stable long-time slope, uncertainty
  from blocks/origins, and enough independent diffusion events; do not fit the
  ballistic or caged regime.
- **RDF/pair correlation:** record pair order, cutoff, bin width,
  normalization, cell fluctuations, and excluded equilibration. Verify the
  large-r normalization where the finite cell permits it.
- **VACF/vibrational DOS:** record velocity source, sampling interval,
  component/species selection, mean removal, correlation/window length,
  taper/zero-padding, transform convention, and frequency units. Spectral
  peaks are not automatically normal modes or thermodynamic phonons.
- **bond distributions:** define periodic-neighbor handling, pair/angle
  selectors, cutoff logic, and whether coordination changes are allowed.
- **trajectory export:** confirm atom order, cell, time metadata, and unit
  preservation; a viewable animation is not evidence of equilibrium.

## Operational heuristics

These are experience-layer defaults for planning, not official VASPKIT facts:

- keep generation, VASP execution, and VASPKIT extraction in separate
  directories or immutable stages; copy only a hash-checked bundle into the
  extraction scratch directory;
- run a new menu task interactively once, capture every prompt and created
  file, then freeze a version-specific `cmd.in`; do not extrapolate a dialogue
  from an adjacent task number;
- compare file inventories and hashes before and after each task because many
  menu utilities overwrite conventional names;
- treat Fermi-surface topology, optical spectra, effective masses, work
  functions, and transport fits as separate observables with separate
  convergence studies;
- keep raw spin channels, tensor components, atom/orbital projections, and
  unshifted energy references even when the presentation layer sums or shifts
  them;
- if two official pages disagree, prefer a blocked plan plus an exact-version
  transcript over a guessed batch command.

## Failure triage

| Symptom | Likely class | Required action |
|---|---|---|
| task id opens a different menu | documentation/binary version drift | stop automation; capture banner, help, menu, and prompts; add an exact-version profile |
| expected table missing but task reaches plotting | optional plotting/runtime issue or wrong output assumption | inspect transcript and file inventory; separate numerical output from plotting dependencies |
| Fermi level or band gap differs between tasks | mixed parent files or energy-reference override | compare source hashes, `DOSCAR`/`OUTCAR` Fermi source, `FERMI_ENERGY.in`, and `SET_FERMI_ENERGY_ZERO` |
| PDOS/projected band columns look incomplete | incompatible `LORBIT`, missing projection file, spin/SOC layout, or selector mismatch | return to the parent and preserve exact projection semantics |
| Fermi surface changes dramatically with small mesh/reference changes | unresolved numerical/topological convergence | refine the mesh, test the energy reference, and report the instability rather than one surface |
| work-function plateau slopes or differs by slab side | insufficient vacuum, dipole/asymmetry, charged slab, or wrong potential definition | repair/reconverge the VASP parent; VASPKIT averaging cannot fix it |
| optical spectrum has only a few points or unstable peaks | insufficient frequency grid/bands/k points, parse mismatch, or broadening issue | audit `vasprun.xml`, parent settings, exact menu, grid, and tensor output |
| MD diffusion is negative, window-dependent, or based on few events | non-diffusive regime, wrapping error, short trajectory, or bad fit interval | re-evaluate unwrapping/time mapping and extend independent sampling before interpretation |
