# CP2K execution and executable map

## Validation state

The maintainer machine had no `cp2k` or `cp2k.psmp` in `PATH` on
2026-07-18. The commands below follow the pinned official CP2K 2026.2 manual
snapshot, especially “First calculation” and “Troubleshooting”, but were not
executed on that machine.

## Choose and identify the build

The official current manual lists:

| Executable | Build meaning |
|---|---|
| `cp2k.psmp` | MPI plus OpenMP optimized build |
| `cp2k.pdbg` | MPI plus OpenMP debug build |
| `cp2k.ssmp` | serial/OpenMP optimized build |
| `cp2k.sdbg` | serial/OpenMP debug build |

Older installations and site modules may use other suffixes such as `popt` or
`sopt`. Record the actual version/build banner, executable hash, data directory,
linked libraries/accelerator support, and MPI/OpenMP layout. Do not select a
binary by suffix alone.

```text
command -v cp2k.psmp
command -v cp2k.ssmp
```

The official first-calculation command is:

```text
OMP_NUM_THREADS=1 cp2k.psmp -i project.inp -o project.out
```

For an MPI build, the official guide gives this shape:

```text
mpirun -np <MPI_RANKS> -x OMP_NUM_THREADS=<THREADS> \
  cp2k.psmp -i project.inp -o project.out
```

Launcher/environment syntax is MPI- and scheduler-specific. Capture CLI
stderr separately when the site wrapper permits it. The `-o` file is CP2K's
main log target; do not concatenate retries into it.

## Input and side-effect inventory

Before launch, recursively resolve and hash all input-owned data:

- main `.inp` and every `@INCLUDE` or preprocessor source;
- coordinate/topology files;
- basis-set and pseudopotential data files selected by `BASIS_SET_FILE_NAME`,
  `POTENTIAL_FILE_NAME`, and `KIND`;
- dispersion, force-field, QM/MM, or method-specific parameter data;
- intended `EXT_RESTART`, wavefunction, trajectory, cell, or velocity parent.

The `GLOBAL/PROJECT` name and `PRINT` sections control many output names and
volumes. Inventory the work directory before and after launch rather than
assuming a universal output list. Common artifacts include the main `.out`,
restart input, wavefunction restart, trajectory, cell, force, velocity, band,
DOS/PDOS, cube, and task-specific files.

## Run-type and method ownership

| Goal | Decisive CP2K input surface |
|---|---|
| Static energy/SCF | `GLOBAL/RUN_TYPE ENERGY` plus `FORCE_EVAL` |
| Forces | `RUN_TYPE ENERGY_FORCE` and force output evidence |
| Geometry optimization | `RUN_TYPE GEO_OPT` plus `MOTION/GEO_OPT` |
| Cell optimization | `RUN_TYPE CELL_OPT` plus `MOTION/CELL_OPT` |
| Molecular dynamics | `RUN_TYPE MD` plus `MOTION/MD` |
| NEB/replica path | `RUN_TYPE BAND` plus `MOTION/BAND` and replica structures |
| Vibrational analysis | `RUN_TYPE VIBRATIONAL_ANALYSIS` plus its displacement/response controls |
| Electronic bands/DOS/PDOS | accepted Quickstep ground state plus task-specific `DFT/PRINT` sections and sampling |
| Hybrid/DFT+U/dispersion/post-HF | corresponding method sections under `DFT` or the exact method module, with additional evidence profiles |

The executable is usually the same; `RUN_TYPE` and nested sections determine
the calculation. A parser-recognized `RUN_TYPE` is not proof every required
section or build feature is valid.

## High-use native recipes

### Static ENERGY or ENERGY_FORCE

```text
OMP_NUM_THREADS=<T> cp2k.psmp -i static.inp -o static.out
```

Require matching coordinates, cell/periodicity, basis and potential files,
charge/multiplicity, SCF settings, grid/k points, XC/corrections, and Poisson
boundary. After launch verify program start/end, SCF state, energy/force marker,
warnings, actual version, and requested print artifacts.

### GEO_OPT and CELL_OPT

```text
mpirun -np <N> -x OMP_NUM_THREADS=<T> \
  cp2k.psmp -i optimize.inp -o optimize.out
```

Verify the requested optimizer, constraints, force/stress thresholds, maximum
steps, final structure/cell, and explicit stop reason. Follow with a separate
accepted static calculation when the claimed observable requires it. Bind any
restart to the exact parent `.restart`/wavefunction/structure hashes.

### Molecular dynamics

```text
mpirun -np <N> -x OMP_NUM_THREADS=<T> \
  cp2k.psmp -i md.inp -o md.out
```

Verify ensemble, thermostat/barostat chains, timestep, number of steps,
temperature/pressure definitions, constraints, periodicity, restart velocities,
energy drift, equilibration, sampling uncertainty, and complete trajectory.
Technical completion is not evidence that the trajectory is statistically
adequate.

### BAND/NEB

```text
mpirun -np <N> -x OMP_NUM_THREADS=<T> \
  cp2k.psmp -i neb.inp -o neb.out
```

Require endpoints and all replicas, common atom mapping/cell/method, spring and
tangent settings, optimizer/climbing-image state, per-replica SCF and force
evidence, restart lineage, and saddle validation. One main-output termination
marker cannot validate every replica.

### Vibrational analysis

```text
mpirun -np <N> -x OMP_NUM_THREADS=<T> \
  cp2k.psmp -i vib.inp -o vib.out
```

Bind the accepted optimized parent, displacement settings, masses, constraints,
symmetry, SCF/force thresholds, numerical differentiation, and all displacement
subtasks. Check translational/rotational modes, imaginary modes, unit
conventions, and completeness before thermochemical interpretation.

### Bands, DOS, and PDOS

```text
mpirun -np <N> -x OMP_NUM_THREADS=<T> \
  cp2k.psmp -i electronic-analysis.inp -o electronic-analysis.out
```

Use the exact CP2K manual entries for `KPOINTS` and task-specific print
sections. Preserve uniform mesh versus line path, spin, Fermi/energy reference,
projection basis, broadening, empty states, SCF state, and output filename/unit
metadata. A generated table or plot does not establish electronic convergence.

## Completion record

Only state that native CP2K execution passed after recording:

1. executable/banner/build and MPI/OpenMP launcher;
2. exact input plus every included/external data hash;
3. exact parent/restart identity;
4. one coherent main output and separate CLI errors;
5. requested run-type completion, SCF state, warnings, and task artifacts;
6. numerical and physical evidence independent of normal termination.

The official manual mirror, resolver, input auditor, and public negative
fixtures do not substitute for running the exact local executable.

## Official mirrored sources

- local provider-cache `first-calculation.md` — installed executable variants
  and `-i/-o` commands; locate it from `references/manual-cache-route.md`.
- local provider-cache `troubleshooting.md` — stdout/stderr and MPI-launch
  examples; locate it from `references/manual-cache-route.md`.
- `references/official-source-policy.md` — exact version/live source policy.
- `references/capability-coverage-matrix.md` — automated versus documented
  surfaces.
