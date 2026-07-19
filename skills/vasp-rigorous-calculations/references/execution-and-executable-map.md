# VASP execution and executable map

## Validation state

The maintainer machine had no `vasp_std`, `vasp_gam`, or `vasp_ncl` in `PATH`
on 2026-07-18. The invocation patterns below are grounded in the official VASP
Wiki and official tutorials, but were not executed on that machine. VASP is
licensed software; this repository does not distribute or install it.

## Identify the executable and build

Official VASP 6 builds normally provide:

| Executable | Intended route |
|---|---|
| `vasp_std` | Standard collinear/general k-point calculations |
| `vasp_gam` | Gamma-only optimized build; use only when the actual sampling is Gamma-only and the method is compatible |
| `vasp_ncl` | Noncollinear magnetism and SOC; official `LSORBIT` and `LNONCOLLINEAR` pages require this executable |

Site/GPU executable names may differ. Do not infer capability from a filename;
record the normal-output version/build banner and executable hash.

```text
command -v vasp_std
command -v vasp_gam
command -v vasp_ncl
```

VASP reads fixed filenames in its working directory rather than an input
filename argument. The official tutorial uses:

```text
cd <isolated-case-directory>
mpirun -np <MPI_RANKS> vasp_std > vasp.stdout 2> vasp.stderr
```

The MPI launcher/resource flags are site-specific. An OpenMP-enabled build also
requires an intentional `OMP_NUM_THREADS` and placement policy. Match the
launcher to the scheduler allocation and benchmark without weakening scientific
settings.

## Working-directory contract

Before launch, inventory and hash:

- `INCAR`;
- `POSCAR`;
- `POTCAR` identity/metadata and hash without exposing licensed content;
- `KPOINTS`, including whether it is explicit, automatic, Gamma-only, uniform,
  line-mode, or weighted/zero-weight mixed;
- any intended restart `WAVECAR`, `CHGCAR`, `CONTCAR`, or method-specific
  parent artifact.

Capture `vasp.stdout` and `vasp.stderr` separately. VASP may create or update
`OUTCAR`, `OSZICAR`, `vasprun.xml`, `CONTCAR`, `WAVECAR`, `CHGCAR`,
`DOSCAR`, `EIGENVAL`, `PROCAR`, `LOCPOT`, `ELFCAR`, and other task-dependent
files. Presence of a filename is not proof it is complete, current, or enabled
with the intended semantics.

Never make the first trial in the only copy of a calculation and never append
stdout from retries into one apparent run.

## High-use execution chains

### Relaxation followed by production static

```text
cd relax
mpirun -np <N> vasp_std > vasp.stdout 2> vasp.stderr

cd ../static
# create a reviewed POSCAR from the accepted relax/CONTCAR
mpirun -np <N> vasp_std > vasp.stdout 2> vasp.stderr
```

Treat the static run as a child with explicit structure and restart hashes.
Verify the relaxation stop reason, final forces/stress, constraints, cell policy,
and state continuity. Re-audit all four static inputs; copying `CONTCAR`,
`WAVECAR`, or `CHGCAR` does not make them compatible automatically.

### Gamma-only and SOC/noncollinear selection

```text
mpirun -np <N> vasp_gam > vasp.stdout 2> vasp.stderr
mpirun -np <N> vasp_ncl > vasp.stdout 2> vasp.stderr
```

The first line is only for a genuinely Gamma-only compatible task. Use
`vasp_ncl` for `LSORBIT=.TRUE.` or `LNONCOLLINEAR=.TRUE.`. Preserve vector
magnetization conventions, `SAXIS`, symmetry, complex wavefunction ancestry,
and the exact executable. Do not construct a nonexistent “Gamma+ncl”
substitution.

### Conventional band structure

1. Run an accepted SCF calculation on a converged uniform mesh.
2. Create a separate band directory with the same structure, POTCAR identity,
   method/state settings, and a line-mode path.
3. Bind the parent `CHGCAR` when using the fixed-density route such as
   `ICHARG=11`.
4. Run the compatible executable:

```text
mpirun -np <N> vasp_std > vasp.stdout 2> vasp.stderr
```

Use `vasp_ncl` instead when the band task is SOC/noncollinear. Verify the path,
labels, number of bands, parent charge identity, energy reference, spin/SOC
semantics, and state continuity. A line path cannot prove global extrema.

### DOS and projected DOS

Use a separate accepted static/NSCF calculation with a converged uniform mesh,
intentional occupations/integration settings, `NEDOS`/energy window, enough
empty bands, and the required `LORBIT` projection configuration:

```text
mpirun -np <N> vasp_std > vasp.stdout 2> vasp.stderr
```

Check `DOSCAR`/`vasprun.xml` completion, Fermi reference, spin sign, projection
basis, atom order, normalization, and electron-count consistency where
applicable. A band-path directory is not a valid replacement for a DOS mesh.

### Hybrid band structure

Run the hybrid-compatible executable with a KPOINTS set that preserves the
weighted self-consistent mesh and adds the intended zero-weight path:

```text
mpirun -np <N> vasp_std > vasp.stdout 2> vasp.stderr
```

Use `vasp_ncl` for hybrid+SOC/noncollinear. Preserve weighted versus zero-weight
points, symmetry, `LHFCALC`/screening/exchange settings, restart ancestry,
empty-state convergence, and exact path construction.

### VASP NEB

The conventional directory layout has root control files and ordered image
directories (`00` through `N+1`), each containing a mapped `POSCAR`. Launch the
chosen VASP executable from the NEB root using the site launcher:

```text
mpirun -np <N> vasp_std > vasp.stdout 2> vasp.stderr
```

Audit every image and endpoint, atom ordering/mapping, consistent cell and
method, per-image electronic convergence, tangent/spring settings, force
criterion, climbing-image state, restart ancestry, and the saddle-point
validation. A root-directory OUTCAR check cannot validate the full path.

## Completion evidence

For every native run require:

1. exact executable/build banner and launcher;
2. one pre-run four-input inventory with hashes and non-sensitive POTCAR
   identity;
3. one coherent stdout/stderr/OUTCAR/vasprun.xml run, not concatenated retries;
4. normal termination plus electronic and task-specific ionic/response evidence;
5. output identity, expected side effects, units, state, and restart lineage;
6. separate numerical and physical validation for the claimed observable.

Only say “native VASP execution passed” after an actual licensed executable ran.
The input auditor, official Wiki mirror, and synthetic fixtures do not establish
that claim.

## Official entry points

- Installation, executable targets, and tests:
  <https://www.vasp.at/wiki/Installing_VASP.6.X.X>
- Official molecule tutorial showing `mpirun -np 2 vasp_std`:
  <https://www.vasp.at/tutorials/latest/molecules/part1/>
- Official executable test configuration:
  <https://www.vasp.at/wiki/Testsuite>
- Official hybrid MPI/OpenMP invocation:
  <https://www.vasp.at/wiki/Combining_MPI_and_OpenMP>
- Official SOC/noncollinear executable requirements:
  <https://www.vasp.at/wiki/LSORBIT> and
  <https://www.vasp.at/wiki/LNONCOLLINEAR>
