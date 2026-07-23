# Input formats and cross-program handoffs

This reference translates Multiwfn manual section 2.5 and the periodic-system
guidance in section 2.9 into fail-closed intake checks. Statements labelled
**Manual fact** summarize the pinned official manual. Statements labelled
**Operational gate** are repository policy or practitioner safeguards; they
are not claims made by the Multiwfn authors.

## Contents

1. Start from the requested observable
2. Capability matrix
3. Producer-specific routes
4. Periodic systems
5. Paired excitation files
6. Private source manifest
7. Handoff checklist

## Start from the requested observable

Do not choose a file merely because Multiwfn recognizes its suffix. First list
the information the analysis consumes, then choose the richest traceable export
that contains it.

| Requested work | Minimum information | Prefer | Reject or qualify |
|---|---|---|---|
| Density, gradient, Laplacian, ELF, LOL, RDG | GTF wavefunction and coordinates, or an explicitly identified grid for grid-only operations | `.mwfn`, eligible `.fch/.fchk`, well-formed `.wfx`; a producer-native grid when the task is strictly grid processing | structure-only files; grids whose field, units, cell, or ordering are unknown |
| Orbital plots or orbital-dependent functions | orbital coefficients, occupations, spin convention, GTFs, coordinates | `.mwfn`, `.fch/.fchk`, validated Molden/program export | `.wfn/.wfx` when virtual orbitals are needed |
| Mulliken/SCPA composition, Mayer order, PDOS/OPDOS | basis-function identity plus orbital/density data | `.mwfn`, `.fch/.fchk`, validated Molden/program export | `.wfn/.wfx`; structure-only and grid files |
| QTAIM/topology | differentiable scalar field, coordinates, ECP/EDF convention, numerical search settings | GTF wavefunction with explicit electron/core treatment | a picture or cube without evidence that derivatives/search are adequate |
| Charge fitting to ESP | wavefunction and a documented ESP definition, fitting surface/grid, constraints | a producer export whose electron/core and solvent convention is known | coordinates plus pre-existing charges when the task is to derive new charges |
| DOS/PDOS/OPDOS | molecular orbitals and energies; basis composition for projected/overlap variants | basis-bearing wavefunction source | structure-only files; smoothed curves without raw levels and broadening settings |
| Vibrational, electronic, Raman, ECD, NMR spectrum | supported program output or exact special transition text | original converged output plus producer input/checkpoint lineage | `.fch`, Molden, `.wfn`, or `.wfx` alone |
| Hole/electron or transition-density analysis | matching basis/MO source and excitation coefficient source | two files from the same calculation and geometry | files from different geometries, methods, state orderings, or restarts |

**Operational gate:** write a one-line eligibility decision before planning a
menu path, for example: `eligible because fchk contains basis identity, MOs,
occupations, and coordinates required by Mayer analysis`. If any required item
is unknown, stop rather than let suffix recognition stand in for evidence.

## Capability matrix

The table is intentionally about information content, not general file quality.

| Family | Formats named by the pinned manual | Coordinates | Grid | GTF wavefunction | Basis-function identity | Virtual orbitals | Important boundary |
|---|---|---:|---:|---:|---:|---:|---|
| Full wavefunction and basis | `.mwfn`, `.molden`, `.fch/.fchk`, `.chk`, `.gbw`, `.gms` | yes | no | yes | yes | normally yes | converter and producer conventions still matter |
| GTF wavefunction | `.wfn`, `.wfx` | yes | no | yes | no | no | adequate for many real-space functions, not basis-space composition |
| NBO plot set | `.31` with a matching `.32`-`.40` file | yes | no | yes | no | task-dependent | use NBO/NLMO orbitals only for meaningful real-space interpretation |
| Structure only | `.pdb`, `.xyz`, `.mol`, `.sdf`, `.mol2`, `.gro`, `.cif`, `.mop`, supported program inputs/outputs, POSCAR, Turbomole `coord` | yes | no | no | no | no | geometry is not electronic structure |
| Coordinates and charges | `.chg`, `.pqr` | yes | no | no | no | no | imported charges are assigned data, not newly derived populations |
| Grid with structure | cube, CHGCAR/CHG, ELFCAR, LOCPOT | yes | yes | no | no | no | record field meaning, units, cell, spin/channel, and producer flags |
| Grid only | `.vti`, `.grd`, `.dx` | no | yes | no | no | no | atom identity and wavefunction lineage are absent |
| Special text | supported program outputs and strict task-specific text | task-dependent | no | no | no | no | parser eligibility belongs to the exact function and version |

**Manual fact:** `.mwfn` is designed as a strict and extensible exchange format
and is the manual's preferred general interchange. That preference does not
make an unverified conversion lossless.

## Validate the producer-specific route

### Gaussian-style checkpoints

- **Manual fact:** `.fch/.fchk` contains basis functions, GTF information,
  coordinates, occupied and virtual orbitals. A direct `.chk` route depends on
  a configured `formchk` executable.
- **Operational gate:** preserve the original input/output, checkpoint export
  command, producer version, and hashes. Treat `formchk` as a separate adapter
  with its own version and stderr.
- **Manual fact:** a post-HF calculation label does not guarantee that a
  formatted checkpoint contains correlated natural orbitals; it may still
  contain the SCF orbitals unless an appropriate natural-orbital procedure was
  used.
- **Operational gate:** verify occupations and orbital type from the producer
  output. Do not relabel SCF orbitals as natural orbitals from the job method.

### Molden and program-native orbital exports

- **Manual fact:** Molden variants are not uniformly standardized. The manual
  names supported producer/convention combinations, including Molpro, ORCA,
  xtb, Dalton, NWChem under stated restrictions, MRCC, deMon2k, BDF, and CP2K.
- **Manual fact:** the manual recommends a standardizing converter such as
  `molden2aim` for producers whose Molden dialect is not directly compatible.
- **Operational gate:** record spherical versus Cartesian basis convention,
  basis order, normalization, spin/occupation convention, ECP nuclear charge,
  and atom ordering. Compare electron count and several orbital energies or
  occupations against the producer output before analysis.
- **Manual fact:** direct ORCA `.gbw` intake depends on `orca_2mkl`. Recent ORCA
  `[Pseudo]` information can address ECP charge semantics only when the reader
  and export version support it.
- **Operational gate:** never treat converter success as semantic validation;
  check the converted header, electron count, atom count, charge/multiplicity,
  basis size, orbital count, and spin channels.

### `.wfn` and `.wfx`

- **Manual fact:** `.wfn` carries occupied orbital/GTF/coordinate information
  but lacks virtual orbitals and basis-function identity and has angular
  momentum limitations.
- **Manual fact:** `.wfx` has higher precision and higher-angular-momentum
  support. For ECP calculations it may carry electron-density functions (EDF)
  representing core density, but not every non-Gaussian producer writes EDF.
- **Manual fact:** missing EDF changes density and its derivatives, entropy,
  RDG, `sign(lambda2)rho`, and density topology. It does not change ESP or
  explicitly orbital-dependent functions such as kinetic-energy density and
  ELF in the same way.
- **Operational gate:** integrate the density over a sufficiently converged
  whole-space grid and compare it with the expected valence-plus-core electron
  convention. Record whether EDF exists; never silently mix all-electron and
  valence-only topology or basin results.

### Structure and grid formats

- **Manual fact:** CIF import needs explicit symmetry operations when symmetry
  expansion is required. QE structure import supports the manual's stated
  `ibrav=0` route; POSCAR supplies structure, not a wavefunction.
- **Manual fact:** CHGCAR/CHG supplies charge-density grids and can include spin
  information; ELFCAR supplies ELF; LOCPOT supplies a potential whose exact
  meaning depends on producer settings such as `LVHAR`.
- **Operational gate:** record coordinate unit, grid value unit, total versus
  spin channel, cell vectors, origin, axis vectors, point counts, periodic
  convention, atom order, augmentation/content convention, and producer flags.
  Refuse a renamed or hand-edited grid whose semantics cannot be reconstructed.
- **Operational gate:** when combining grids in main function 13, require exact
  equality of origin, three grid vectors, and point counts. Geometrically
  similar grids are not index-compatible.

## Treat periodic systems as a separate method choice

**Manual fact:** the pinned manual distinguishes two routes:

1. analyze a finite cluster and demonstrate size/boundary convergence; or
2. use a directly supported periodic wavefunction route, formally centered on
   CP2K output under the manual's restrictions.

For the direct CP2K route:

- write MO Molden data with the documented numerical precision such as
  `NDIGITS 9`;
- supply the cell through a recognized `[Cell]` record or companion cell file;
- preserve effective nuclear charges and `[Nval]` semantics when
  pseudopotentials are present;
- record `ifdoPBCxyz`, `PBCnxnynz`, the actual cell source, and the set of
  periodic images used by the selected analysis;
- restrict work to functions the pinned manual explicitly states are tested
  for periodic wavefunctions;
- do not request periodic ESP from a periodic wavefunction where the manual
  states that route is unsupported.

**Operational gate:** do not infer periodicity from a filename or unit cell in
a visualization file. A cluster cutout is not equivalent to a periodic
calculation; report termination, charge compensation, cluster size, and the
observable's convergence with those choices.

## Match paired files before excitation analysis

Main function 18 requires a basis/MO source and a separate excitation source.
Before loading either file, compare:

- atom count, atom order, geometry coordinates and units;
- method, basis/ECP, charge, multiplicity, and solvent/environment model;
- restricted/unrestricted spin convention and MO counts;
- calculation identifier, restart lineage, and producer version;
- requested state number, energy, oscillator/rotatory strength, and printed
  configuration list;
- coefficient-print threshold and the normalization convention.

Reject a pair when only the basename or approximate excitation energy matches.
For Gaussian, ORCA, CP2K, BDF, or another supported producer, follow the exact
version-specific export route in the pinned manual. ORCA CIS/TDA print options,
ORCA TDDFT JSON conversion, and truncated sTDA/sTDDFT configuration lists are
distinct routes and must not be conflated.

## Write a private source manifest

Keep real paths and unpublished results outside Git. A run manifest should at
least contain:

```yaml
producer:
  code: <code>
  version: <exact version>
  method: <method>
  basis_or_pseudopotential: <identity, not licensed contents>
  charge: <integer>
  multiplicity: <integer>
source:
  format: <format>
  basename: <safe basename>
  sha256: <64 lowercase hex>
  bytes: <integer>
  export_command: <redacted command or adapter id>
  converter_version: <version or null>
semantics:
  atom_order_verified: true
  electron_count_expected: <number>
  electron_count_loaded: <number>
  spin_convention: <restricted, alpha-beta, other>
  ecp_edf_convention: <all-electron, valence-only, EDF-present, not-applicable>
  periodic: <true or false>
  cell_source: <source or null>
```

The repository's current `normalized-dataset@1.0` contract has no dedicated
Multiwfn code enum. Until that shared contract changes, a normalized
Multiwfn-derived dataset must use `code: mixed` and preserve the producer and
Multiwfn identities in provenance metadata. This is an interface limitation,
not permission to claim that a mixed label establishes scientific validity.

## Handoff checklist

Before sending an artifact to another program or analyst, provide:

1. source and converter hashes, exact versions, and original producer lineage;
2. Multiwfn banner/update date, distribution identity, executable/settings
   hashes, full/noGUI mode, command stream, stdout, and stderr;
3. selected function, every response after the documented prefix, and all
   task parameters;
4. artifact filename, SHA-256, bytes, format, units, coordinate/cell/grid
   convention, and atom/orbital/state ordering;
5. technical closure checks and scientific applicability/convergence checks as
   separate fields;
6. limitations such as missing EDF, truncated configurations, basis
   sensitivity, cluster approximation, or broadening dependence.

Do not hand off only a PNG, isosurface, smoothed curve, or charge column when
the downstream interpretation depends on the underlying numerical artifact.
