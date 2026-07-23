# Quantum ESPRESSO execution and program map

## Validation state

The maintainer machine had no `pw.x`, `ph.x`, or `neb.x` in `PATH` on
2026-07-18. The commands below are grounded in the versioned official QE user
guides mirrored by this Skill, but they were not executed on that machine.
Record a native run separately from a documented invocation.

## Install and identify the build

Use an official QE release or a site-provided build and put the required
executables in `PATH`. Record the exact QE version/banner from each program's
normal output, build/accelerator identity, executable hash, MPI/OpenMP launcher,
and linked pseudopotential set. Do not assume all executables came from the same
build merely because their names resolve.

```text
command -v pw.x
command -v ph.x
command -v neb.x
```

The official user guide uses `-i`, `-in`, `-inp`, or `-input` followed by an
input filename and recommends file input when MPI redirection is unreliable.
Prefer an explicit input option and separate stdout/stderr:

```text
mpirun -np <MPI_RANKS> pw.x -in scf.in > scf.out 2> scf.err
```

Preserve both files. A `qe_guard audit` completion check requires `--output scf.out --stderr scf.err`; signalling IEEE floating-point flags in stderr are blocking runtime diagnostics even when stdout contains `JOB DONE.`.

The MPI launcher and resource flags are site-specific. Do not copy
`<MPI_RANKS>` or parallelization flags until they match the scheduler
allocation and build.

## Program ownership

| Goal | Primary QE programs | Required ancestry |
|---|---|---|
| SCF, NSCF, relax, vc-relax, line-mode bands | `pw.x` | structure and UPF files; NSCF/bands inherit compatible SCF `prefix`/`outdir` |
| Band sorting/symmetry labels | `bands.x` | completed `pw.x` band calculation |
| Total DOS | `dos.x` | completed uniform-mesh NSCF data, not a line path |
| PDOS and projections | `projwfc.x` | completed projection-compatible NSCF data |
| Charge density, potentials, wave-function grids | `pp.x` and task-specific grid tools such as `average.x` | matching completed `pw.x` data |
| DFPT phonons | `ph.x` | accepted ground-state `pw.x` data with matching `prefix`/`outdir` |
| Real-space force constants and interpolated phonons | `q2r.x` then `matdyn.x`; `dynmat.x` for selected dynamical matrices | complete compatible `ph.x` q-point set |
| NEB | `neb.x` | one NEB input containing PATH and PW engine sections, or the documented image-file mode |
| Hubbard parameters | `hp.x` | matching SCF/response prerequisites from the exact manual |
| Wannier interface | `pw2wannier90.x` | compatible `pw.x` and Wannier90 inputs |

“Program exists” is not proof that the requested workflow or build option is
available. Resolve the exact program manual through
`official-manual-index.md`.

## High-use command chains

### SCF, relaxation, and restart

```text
mpirun -np <N> pw.x -in scf.in > scf.out 2> scf.err
mpirun -np <N> pw.x -in relax.in > relax.out 2> relax.err
```

Before launch, pass the input guard, verify every UPF file and `pseudo_dir`,
ensure `outdir` is writable and isolated, and bind the launcher/resource
request. After launch, require one coherent version/start/end record and
`JOB DONE.` plus task-specific electronic/ionic evidence. A scheduler exit code
or `JOB DONE.` alone does not establish convergence.

For restart, preserve the exact `prefix`, `outdir` save tree, input, code
version, UPFs, and restart settings. Do not combine stdout from retries.

### Conventional bands

```text
mpirun -np <N> pw.x -in scf.in > scf.out 2> scf.err
mpirun -np <N> pw.x -in bands-pw.in > bands-pw.out 2> bands-pw.err
bands.x -in bands.in > bands.out 2> bands.err
```

The second `pw.x` input uses the intended line path and inherits the accepted
SCF data. `bands.x` postprocesses the eigenvalues. Preserve path coordinates,
labels, spin/SOC mode, energy reference, and the `bands.x` output filename.
Line-path bands cannot establish a Brillouin-zone-wide gap without additional
sampling.

### DOS and PDOS

```text
mpirun -np <N> pw.x -in scf.in > scf.out 2> scf.err
mpirun -np <N> pw.x -in nscf.in > nscf.out 2> nscf.err
dos.x -in dos.in > dos.out 2> dos.err
projwfc.x -in projwfc.in > projwfc.out 2> projwfc.err
```

Use a uniform NSCF mesh suitable for integration rather than a band path.
Verify occupations/smearing or tetrahedron policy, energy window/grid,
normalization, projections, spin convention, empty states, and convergence.
`dos.x` and `projwfc.x` must reference the same `prefix`/`outdir` lineage.

### DFPT phonons and dispersion

```text
mpirun -np <N> pw.x -in scf.in > scf.out 2> scf.err
mpirun -np <N> ph.x -in ph.in > ph.out 2> ph.err
q2r.x -in q2r.in > q2r.out 2> q2r.err
matdyn.x -in matdyn.in > matdyn.out 2> matdyn.err
```

Run `q2r.x` only after the required q mesh is complete and compatible. Preserve
q-point weights, irreducible/full-grid reconstruction, non-analytic correction
inputs, dimensional electrostatics, acoustic-sum-rule choice, masses, and
Fourier-interpolation settings. A Γ-only calculation is not a phonon
dispersion.

### NEB

```text
mpirun -np <N> neb.x -in neb.in > neb.out 2> neb.err
```

The official NEB guide explicitly states that `neb.x` does not read standard
input, so `neb.x < neb.in` is invalid. An alternative documented mode uses
`-input_images <N>` with `neb.dat` and `pw_X.in` files. Verify endpoints,
image count and mapping, path settings, per-image SCF/force convergence,
climbing-image behavior, restart ancestry, and saddle validation.

## Completion record

For every stage retain:

- executable hash/version and launcher;
- exact input and all referenced UPFs;
- `prefix`, `outdir`, parent save-tree identity, and restart state;
- stdout and stderr as separate artifacts;
- scheduler exit/resource record when present;
- program-specific output files and their hashes.

Only say “native QE execution passed” when the exact executable actually ran.
The guard and official manual lookup can validate documented syntax and bounded
output evidence without supplying that native-installation claim.
