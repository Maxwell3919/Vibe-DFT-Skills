# SIESTA execution and program map

Use this map before writing a shell command. It is pinned to the SIESTA 5.4
manual family used by this Skill. It teaches which executable owns each stage;
it does not authorize execution and does not prove that a local binary has the
documented build features.

## Evidence and current native state

Primary official sources:

- [SIESTA 5.4 reference manual](https://docs.siesta-project.org/projects/siesta/en/5.4/reference/siesta.html), especially **Parallel operation**, **Execution of the program**, **Program output**, and the task-specific FDF sections;
- [official first-encounter tutorial](https://docs.siesta-project.org/projects/siesta/en/latest/tutorials/basic/first-encounter/index.html), which demonstrates the FDF/pseudopotential inputs, both launch forms, and common output files;
- [official utility-manual index](https://docs.siesta-project.org/projects/siesta/en/latest/reference/), plus the linked Denchar, Macroave, plstm, TBtrans, and WFS2LDOS manuals;
- official tutorials for [bands](https://docs.siesta-project.org/projects/siesta/en/latest/tutorials/basic/electronic-structure-analysis/bands/index.html), [DOS](https://docs.siesta-project.org/projects/siesta/en/latest/tutorials/basic/electronic-structure-analysis/dos/index.html), and [phonons](https://docs.siesta-project.org/projects/siesta/en/latest/tutorials/basic/vibrational-properties/index.html).

Local probe on 2026-07-19: `siesta`, `tbtrans`, `gnubands`, `Eig2DOS`,
`denchar`, `macroave`, `plstm`, `wfs2ldos`, `fcbuild`, and `vibra` were not
found on `PATH`. Therefore:

```text
documentation_state: official-manual-grounded
recipe_state: documented-command-plan
native_execution_state: not_run
native_output_state: not_available
```

Do not change either native state to passed from a parser fixture, an official
example output, a successful Python unit test, or a command printed by this
document. A future native check must record the executable path, `siesta -v`,
build/parallelization header, command, exit status, stdout/stderr hashes, and
produced-artifact inventory.

## Probe the installation without starting a calculation

Run only when read-only environment inspection is in scope:

```bash
command -v siesta
siesta -v
siesta -h
command -v tbtrans
tbtrans -v
tbtrans -h
```

`-v`/`-version` and `-h`/`-help` are documented for SIESTA 4.1 and later and
for TBtrans. Record the actual output; do not infer MPI, OpenMP, NetCDF, PSML,
ELSI, ELPA, PEXSI, DFT-D3, Lua/flook, or transport support from the executable
name. The SIESTA run header reports version, compiler, libraries, and available
parallelizations and is part of the evidence.

## Native SIESTA launch forms

SIESTA 4.1 and later accepts the FDF file as a positional argument. This is the
preferred unambiguous form in this Skill:

```bash
siesta RUN.fdf > RUN.out 2> RUN.err
```

The historical stdin form remains documented and is required for older builds:

```bash
siesta < RUN.fdf > RUN.out 2> RUN.err
```

SIESTA 4.1+ can write standard output through its own option:

```bash
siesta --out RUN.out RUN.fdf
```

Useful documented command-line overrides are:

```bash
siesta -L alternate_label RUN.fdf > RUN.out
siesta -fdf SCF.MustConverge=true RUN.fdf > RUN.out
siesta -elec electrode.fdf > electrode.out
siesta -V 0.25:eV device.fdf > device-0.25eV.out
```

- `-L` temporarily overrides `SystemLabel`.
- `-fdf` supplies one FDF option string; record every override because the
  command and file together define the effective input.
- `-elec` is a transport-electrode shortcut that forces the documented HS/DE
  outputs; it does not validate an electrode model.
- `-V` supplies a TranSIESTA bias; an omitted unit is interpreted as eV, so
  always write the unit.

Do not silently mix a positional input with shell stdin, and do not use command
line overrides without storing them in the run manifest. A successful process
exit is not completion evidence; inspect the unique run boundaries, failure
messages, SCF status, and the actual effective input.

## Parallel launch forms

The official manual gives the MPI form:

```bash
mpirun -np <MPI_RANKS> siesta RUN.fdf > RUN.out 2> RUN.err
```

For an OpenMP-enabled build:

```bash
OMP_NUM_THREADS=<THREADS> siesta RUN.fdf > RUN.out 2> RUN.err
```

The official OpenMPI hybrid example uses rank placement and thread binding:

```bash
mpirun --map-by ppr:1:socket:pe=8 \
  -x OMP_NUM_THREADS=8 \
  -x OMP_PROC_BIND=true \
  siesta RUN.fdf > RUN.out 2> RUN.err
```

The launcher syntax is scheduler/MPI dependent. Replace `mpirun` with the
site-approved launcher only after reading the cluster profile. Verify that
`MPI_RANKS × OMP_NUM_THREADS` matches the allocation, avoid accidental nested
BLAS oversubscription, and benchmark MPI-only, OpenMP-only, and hybrid layouts
for the actual system. The manual explicitly notes that `OMP_PROC_BIND` can
materially change performance.

## Working-directory inputs and side effects

Before launch, inventory and hash at least:

- the direct `RUN.fdf` and every `%include` or redirected FDF fragment;
- every species pseudopotential named by `ChemicalSpeciesLabel`; official
  tutorials recommend PSML and say the current directory is searched by
  default;
- any explicit basis, coordinates, k-grid, Lua, restart, electrode, Hamiltonian,
  density-matrix, wavefunction, or external-driver file;
- the executable identity and every command-line override.

Never run two cases in one directory. Official tutorials warn that rerunning in
the same folder overwrites outputs. `SystemLabel` controls many names, but it is
not a namespace or an atomic-output guarantee.

Common outputs include:

- redirected standard output plus the effective FDF/default log;
- `SystemLabel.DM` for density-matrix restart;
- `SystemLabel.XV` for cell/coordinates restart and `SystemLabel.FA` for forces;
- `SystemLabel.EIG` and `SystemLabel.KP` for DOS processing;
- `SystemLabel.bands` when a band path is requested;
- optional `.PDOS`, `.RHO`, `.VH`, `.VT`, `.WFSX`, `.HSX`, `.TSHS`, `.TSDE`,
  NetCDF, dynamics, force-constant, and timing files when the corresponding
  FDF options/build features request them.

An expected filename is not evidence that the content is current or complete.
Bind each consumed artifact to its producer run and hash it before downstream
processing.

## Program and task ownership

| Goal | Native owner | Required parent/artifact | Typical output | Status in this Skill |
| --- | --- | --- | --- | --- |
| SCF/static energy, forces, stress | `siesta` with `MD.Steps 0` | FDF, structure, basis, pseudopotentials | standard output, `.DM`, `.FA`, `.EIG`, optional grid files | automated technical audit supported |
| Fixed-cell relaxation | `siesta`; `MD.TypeOfRun` = `CG`, `Broyden`, or `FIRE`, `MD.VariableCell false` | converged electronic state at each step | standard output, `.XV`, `.FA`, restart files | automated fixed-cell core supported |
| Variable-cell relaxation | same executable with `MD.VariableCell true` and stress controls | periodic cell and stress target | relaxed cell/coordinates, stress history | documented/manual evidence only |
| Molecular dynamics | `siesta`; `Verlet`, `Nose`, `ParrinelloRahman`, `NoseParrinelloRahman`, or `Anneal` | initial state/velocities and ensemble controls | trajectory/restart/timing files | documented/manual evidence only |
| Electronic bands | `siesta` produces `.bands`; `gnubands` makes plotting data/script | accepted parent state and explicit `BandLines`/`BandPoints` | `.bands`, converted data, optional `.gplot` | documented/manual evidence only |
| Total DOS | `siesta` produces `.EIG`/`.KP`; `Eig2DOS` broadens them | accepted parent and converged DOS k mesh | text DOS table | documented/manual evidence only |
| PDOS/COOP/COHP/fat bands | `siesta` native blocks or offline `mprop`/`fat`/`eigfat2plot` | compatible `.WFSX`, `.HSX`, projection definition | `.PDOS`, `.EIGFAT`, text tables | documented/manual evidence only |
| Finite-displacement phonons | SIESTA force-constant mode plus `fcbuild`/`vibra`; `gnubands` can plot frequencies | accepted relaxed parent and displacement/supercell plan | `.FC`, `.bands`, `.vectors` | documented/manual evidence only |
| Real-space charge/wavefunctions | `denchar` | `.PLD`, `.DIM`, species `.ion`, plus `.DM` or selected `.WFSX` | 2-D tables or Gaussian cubes | documented/manual evidence only |
| Planar/macroscopic averages | `macroave` | SIESTA grid file such as `.RHO`, `.DRHO`, `.VH`, or `.VT`; `macroave.in` | planar/macroscopic text profiles | documented/manual evidence only |
| STM slice from LDOS | `plstm` | SIESTA LDOS grid | constant-height/current 2-D slice | documented/manual evidence only |
| STM/STS from wavefunctions | `wfs2ldos` | `.PLD`, `.DIM`, `.ion`, linked `.WFSX`, sometimes `.VH`; FFTW build | SIESTA-format LDOS grid | documented/manual evidence only |
| TranSIESTA device SCF | `siesta` itself since 4.1 | electrode/device FDF and compatible electrode Hamiltonians | `.TSHS`, `.TSDE`, transport state | documented/manual evidence only |
| Electronic transport analysis | standalone `tbtrans` | compatible Hamiltonian/electrode files and TBT FDF | NetCDF-4 transport data and log | documented/manual evidence only |
| Phonon transport | `phtrans` build variant | dynamical matrices/electrodes | transport data | documented/manual evidence only |

`MD.TypeOfRun Master/Forces` can wait indefinitely without an external driver;
do not use it as a generic single-point mode. `MD.TypeOfRun Lua` requires a
flook-enabled build. Since 4.1, TranSIESTA is integrated into `siesta`; do not
invent or require a separate `transiesta` executable for a current build.

## High-use documented recipes

### Static SCF or production single point

Make `MD.Steps 0` explicit, audit FDF/species/pseudopotentials, then, only with
execution authorization:

```bash
siesta static.fdf > static.out 2> static.err
```

Check the reported version/build, effective values, SCF convergence, terminal
completion, final energy/forces/stress, and any warnings. Do not use a relaxed
run's last ionic step as a production static result unless the intended protocol
explicitly accepts it.

### Fixed-cell relaxation followed by a static run

1. Run `relax.fdf` with a declared optimizer, `MD.VariableCell false`, explicit
   `MD.Steps` and `MD.MaxForceTol`.
2. Verify the geometry termination and final force norm; preserve `.XV` and the
   final structure.
3. Construct a new static directory/input from the verified final geometry,
   with `MD.Steps 0`; do not reuse a mixed or concatenated log.
4. Run and audit the static result separately.

The same binary owns both stages; task semantics live in FDF and lineage, not in
different executable names.

### Electronic bands

Have `siesta` write a band path, then process the resulting file. An official
tutorial demonstrates:

```bash
siesta bands.fdf > bands.out 2> bands.err
gnubands -G -F -o bands-plot -E 10 -e -20 SystemLabel.bands
gnuplot --persist -e "set grid" bands-plot.gplot
```

Record the band-path convention, reciprocal-cell identity, Fermi/reference
energy, spin convention, energy window, and parent state. A plotted curve alone
does not prove correct ancestry or a converged gap.

### Total DOS

The official tutorial's `Eig2DOS` shape is:

```bash
Eig2DOS -f -e -20 -E 15 -s 0.4 -k SystemLabel.KP \
  SystemLabel.EIG > SystemLabel.dos
```

`-f` shifts the Fermi level to zero; the energy window and Gaussian broadening
are analysis choices. Converge the DOS k mesh and test the broadening rather
than selecting the smoothest plot.

### Finite-displacement phonons

The official phonon tutorial uses this program chain:

```bash
fcbuild < phonon.fdf
siesta < force-constants.fdf > force-constants.out 2> force-constants.err
vibra < phonon.fdf
gnubands < SystemLabel.bands > phonon-bands.dat
```

Treat this as a version-matched documented recipe, not a current native pass.
Verify the exact generated `FC.fdf`/displacement workflow for the installed
version, supercell convergence, displacement amplitude, symmetry handling,
acoustic behavior, and imaginary modes before interpretation.

### Denchar charge or wavefunction grids

The parent SIESTA run must request `WriteDenchar` and provide `.PLD`, `.DIM`, all
species `.ion`, and either `.DM` (charge) or the correct `.WFSX` (wavefunctions):

```bash
denchar < denchar.fdf > denchar.out 2> denchar.err
```

Modern SIESTA distinguishes `fullBZ.WFSX`, `bands.WFSX`, and `selected.WFSX`;
linking the wrong one to `SystemLabel.WFSX` changes the data being plotted.

### TBtrans transport analysis

TBtrans is standalone and accepts either stdin or a positional FDF; the latter
is preferred by its official guide:

```bash
tbtrans transport.fdf > transport.out 2> transport.err
mpirun -np 4 tbtrans transport.fdf > transport-mpi.out 2> transport-mpi.err
```

Documented overrides include `-L`, `-V`, `-D`, `-HS`, and `-fdf`. Verify
Hamiltonian/electrode ancestry, bias, energy contour, k sampling, self-energies,
current conservation, and NetCDF output before extracting a transport claim.

## Completion and scientific limits

For every native stage, require all of the following before calling it
technically complete:

1. exact command, executable hash/path, version and build header recorded;
2. input and side-effect inventory bound to the run;
3. zero process exit plus a unique software completion boundary;
4. no fatal/error markers or concatenated retry logs;
5. task-specific electronic/ionic/transport convergence evidence;
6. expected output content parsed and linked to its producer.

Technical completion does not establish basis, mesh, k-point, cell, time-step,
supercell, energy-window, smearing, or physical-model convergence. Apply the
task checklist and convergence analyzer before making a scientific claim.
