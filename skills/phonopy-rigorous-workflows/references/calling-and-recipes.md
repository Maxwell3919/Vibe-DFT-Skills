# Phonopy 4.3.1 calling guide and practical recipes

## Evidence state

This guide is pinned to official Phonopy tag `v4.3.1` (commit
`baf530aed09071e1221b3c191918a168fc5f1d9b`, released 2026-07-01) and was
checked on 2026-07-19. The local maintainer environment was Darwin arm64 and
contained neither the `phonopy` Python distribution nor any of the 15 official
console scripts. Consequently every call below is `native-not-run`.

Keep these claims separate:

1. a command or option is listed by the tag-pinned official source;
2. an official 4.3.1 page or tutorial shows a usable sequence;
3. the exact local executable accepted the sequence and produced checked data.

Only the first two are available here. Search their machine-readable forms with:

```bash
python3 scripts/phonopy_catalog.py kinds
python3 scripts/phonopy_catalog.py search 'projected DOS'
python3 scripts/phonopy_catalog.py show phonopy-qha
python3 scripts/phonopy_catalog.py plan vasp-finite-displacement
python3 scripts/phonopy_catalog.py probe
```

The catalog and planner never launch Phonopy or a force calculator.

## Installation, version, help, and environment

The official installation page documents a conda route:

```bash
conda install -c conda-forge phonopy
```

The v4.3.1 package manifest requires Python 3.10 or later and lists NumPy,
PyYAML, Matplotlib, h5py, spglib, symfc, and phonors. It declares optional
extras for `seekpath`, `pypolymlp>=0.10.0`, and `cp2k-input-tools`. The install
page also mentions SciPy although it is not a core dependency in the pinned
manifest; record actual package metadata rather than silently reconciling this
documentation drift. `seekpath` is required for `--band auto`.

After an authorized installation, use these read-only checks:

```bash
command -v phonopy
command -v phonopy-init
python -c 'import phonopy; print(phonopy.__version__)'
phonopy -h
phonopy-init -h
```

The tag-pinned parsers do not register `--version`; do not invent that flag.
`phonopy -v` means verbose, not version. All 15 console scripts support help,
but capture their help from the exact installed build before automating a
less-common helper. Record Python and dependency versions, resolved paths,
distribution and executable hashes, platform, architecture, backend banner,
environment lock, and optional extras. On an NFS-mounted HDF5 workflow,
`HDF5_USE_FILE_LOCKING=FALSE` is an official troubleshooting workaround, not a
default to apply globally.

The tag declares these 15 entrypoints:

| Entry point | Role |
|---|---|
| `phonopy-init` | displacement setup, calculator-result collection, direct FC import, symmetry |
| `phonopy` | properties calculated from a phonopy YAML-like file |
| `phonopy-load` | deprecated alias of `phonopy` |
| `phonopy-bandplot` | band plotting and gnuplot-style export |
| `phonopy-calc-convert` | calculator-structure conversion |
| `phonopy-crystal-born` | CRYSTAL Born-data conversion |
| `phonopy-gruneisen` | mode Gruneisen calculations |
| `phonopy-gruneisenplot` | Gruneisen plotting/export |
| `phonopy-pdosplot` | projected-DOS plotting |
| `phonopy-propplot` | thermal-property plotting/export |
| `phonopy-qha` | quasi-harmonic fitting |
| `phonopy-tdplot` | thermal-displacement plotting |
| `phonopy-vasp-born` | VASP dielectric/Born conversion |
| `phonopy-vasp-efe` | VASP electronic states/free energy for QHA |
| `phonopy-qe-born` | QE dielectric/Born conversion |

`phonopy-bandplot --gnuplot` is version-sensitive: the pinned source can emit
the requested stdout and still exit 1. A future adapter must check both the
versioned content and exit semantics. `phonopy-calc-convert` refuses to
overwrite an existing destination; never weaken that behavior with automatic
deletion. `phonopy-propplot` requires an explicit property selector such as
`--cv`, `--entropy`, or `--fe`.

## The v4 command boundary

Phonopy v4 split the old monolithic CLI:

- `phonopy-init` owns `-c`, `--dim`, `-d`, `--rd` for initial snapshots,
  `-f`, `--fz`, `--fc`, and `--symmetry`.
- `phonopy` reads `phonopy_params.yaml`, `phonopy_disp.yaml`, or another
  phonopy YAML-like file and calculates bands, meshes, DOS, thermal properties,
  q-point products, and related observables.
- `phonopy-load` is only a deprecated compatibility alias.

The v4 primitive-matrix default is `auto`; v3 used the input unit cell as-is.
Record the resolved primitive matrix. Use `--pa P` only when deliberately
preserving the v3 identity behavior.

NAC is automatic when a compatible `BORN` file or YAML `nac_params` is found.
The main v4 CLI removed `--nac`; `--nonac` is the explicit opt-out. Rust
`phonors` is the default backend, `--rust` is a deprecated no-op, and
`--legacy-backend` opts into the legacy C path where available.

## VASP finite displacement

Official minimal sequence:

```bash
phonopy-init -d --dim 2 2 2 --pa auto -c POSCAR-unitcell
# Run one fixed-ion VASP force calculation for each POSCAR-###.
phonopy-init --vasp --sp -f disp-{001..N}/vasprun.xml
phonopy --band auto --band-points 101 phonopy_params.yaml
```

Inputs are the unit cell, exact supercell matrix, displacement settings, and
one ordered, completed `vasprun.xml` per displacement. Setup writes
`phonopy_disp.yaml`, `SPOSCAR`, and displaced structures; `--sp -f` writes a
self-contained `phonopy_params.yaml` when collection succeeds.

Route every external calculation through `vasp-rigorous-calculations`. Displaced
supercells must be fixed-ion force calculations, not relaxed structures. Keep
potential identity, ENCUT, k-point density, electronic convergence, smearing,
spin/SOC state, and other force-relevant settings consistent. Require exact
file count and order, structure mapping, completion, force units, and finite
forces. Converge supercell size and displacement amplitude against the target
observable; `2 2 2` and the VASP default displacement are tutorial values.

Common failures include a missing or extra force file, shell expansion in the
wrong order, a relaxed displaced structure, atom reordering, parser-heavy
`vasprun.xml` files containing unnecessary site projections, and a force drift
that contaminates acoustic modes.

## Quantum ESPRESSO finite displacement

Official v4 sequence:

```bash
phonopy-init --qe -d --dim 2 2 2 --pa auto -c NaCl.in
# Complete one pw.x fixed-ion force run for every generated supercell.
phonopy-init --qe --sp -f NaCl-001.out NaCl-002.out ...
phonopy --band auto --band-points 101 phonopy_params.yaml
```

Generated QE structure fragments must be combined with a complete and reviewed
`pw.x` input where necessary; they are not proof of a runnable or scientifically
sufficient calculation. The official interface route expects an explicitly
described cell (`ibrav=0` in the documented workflow). Route each parent through
`qe-rigorous-calculations` and check `pw.x` completion, SCF convergence, forces,
units, atom order, pseudopotentials, cutoffs, k points, occupations, and exact
displacement ancestry. A current official generic option page retains some
`phonopy -f` examples; those are stale for v4 and must be rewritten as
`phonopy-init -f`.

## Direct VASP DFPT force constants

```bash
phonopy-init -d --dim 2 2 2 -c POSCAR-unitcell
# Use SPOSCAR for the accepted VASP IBRION=8 DFPT calculation.
phonopy-init --fc vasprun.xml
phonopy --band auto phonopy_disp.yaml
```

`--fc` is documented as VASP-only. Verify that the accepted `vasprun.xml`
actually contains the Hessian, that the supercell/primitive matrices and atom
mapping match, and that `FORCE_CONSTANTS` has the expected shape. Inspect drift,
symmetry, Gamma acoustic behavior, and questionable eigenvectors. Creation of a
file does not establish a trustworthy force-constant model.

For an existing systematic displacement-force dataset, the v4 calculation
route can write force constants:

```bash
phonopy phonopy_params.yaml --writefc
```

For a random type-2 dataset, select a fitting calculator explicitly:

```bash
phonopy phonopy_params.yaml --fc-calculator symfc --writefc
```

The current parser has no `--symfc` shortcut. Record full versus compact force
constants, solver and version, solver options, primitive-to-supercell mapping,
and dataset type.

## Mesh, DOS, PDOS, bands, and thermal properties

```bash
phonopy --mesh 31 31 31 phonopy_params.yaml
phonopy --mesh 31 31 31 --dos phonopy_params.yaml
phonopy --mesh 41 41 41 --pdos "1, 2" phonopy_params.yaml
phonopy --mesh 31 31 31 -t phonopy_params.yaml
phonopy --band "0 0 0  0.5 0 0  0.5 0.5 0" --band-points 101 phonopy_params.yaml
phonopy --irreps 0 0 0 phonopy_params.yaml
```

Expected products include `mesh.yaml`, `total_dos.dat`, `projected_dos.dat`,
`thermal_properties.yaml`, `band.yaml`, and a symmetry report. The current
Examples page embeds older 2.26.x output banners, so its commands are official
examples but its transcript is not native 4.3.1 evidence.

For meshes, retain the actual mesh written in the result. A length-based mesh
can fall back to a generalized regular grid in v4 when the naive grid breaks
point-group symmetry. Converge the actual grid against each reported observable.
For PDOS, use verbose structural output to establish primitive-cell atom indices
and compare projection sums with the total DOS. Converge smearing and frequency
range. For bands, preserve primitive reciprocal coordinates, labels, segment
boundaries, path density, and the primitive matrix. Do not discard negative
frequencies; inspect their eigenvectors and convergence. For thermal properties,
record the YAML unit block, temperature grid, primitive-cell normalization, mesh
convergence, and imaginary-mode treatment. `--pretend-real` is a testing switch,
not a scientific stability remedy.

Official auxiliary calls include:

```bash
phonopy-bandplot -o band.pdf band.yaml
phonopy-bandplot --gnuplot band.yaml > band.dat
phonopy-pdosplot -i '1 2 4 5, 3 6' -o pdos.pdf projected_dos.dat
phonopy-propplot --cv thermal_properties.yaml
```

Every plot must retain the numerical source hash, units, grouping, labels, and
plot settings. A plot is a presentation product, not a calculation gate.

## VASP and QE non-analytical correction

For a completed and converged VASP response calculation on the exact primitive
structure:

```bash
phonopy-vasp-born vasprun.xml > BORN
# Alternative:
phonopy-vasp-born --outcar OUTCAR POSCAR > BORN
phonopy --band "<checked-path>" phonopy_params.yaml
```

The helper symmetrizes tensors by default; `--nost` disables this. The current
parser has no `--st`. For QE, after matching accepted `pw.x` and Gamma `ph.x`
response runs (`epsil=.true.`):

```bash
phonopy-qe-born NaCl.in NaCl.ph.out > BORN
phonopy --band "<checked-path>" phonopy_params.yaml
```

Check dielectric tensor and Born-charge shapes, independent-atom ordering,
primitive mapping, units, charge neutrality/acoustic sum, and response
convergence. Confirm the `phonopy` log reports NAC activation. Never add the
removed main-CLI `--nac`, and never combine incompatible QE-embedded NAC data
with a second Phonopy correction.

## Random displacements and force-constant fitting

A fixed-amplitude setup sequence from the current parser is:

```bash
phonopy-init --rd 100 --dim 2 2 2 --pa auto \
  --amplitude 0.03 --random-seed 12345 -c POSCAR-unitcell
```

After one accepted force calculation per snapshot:

```bash
phonopy-init --vasp --sp -f force-calcs/disp-{001..100}/vasprun.xml
phonopy phonopy_params.yaml --fc-calculator symfc --writefc
```

Record seed, actual snapshot count, amplitude range, dataset type, file order,
fitter and version, training/validation policy, and output hashes. Converge the
amplitude and sample count against forces and target phonon properties.

Finite-temperature harmonic sampling requires an existing phonon model and is a
calculation-stage operation:

```bash
phonopy phonopy_disp_orig.yaml --rd 1000 --rd-temperature 300 --random-seed 12345
```

Inspect unusually large displacements from low Gamma acoustic modes, output-name
collisions, cutoff choices, and the official algorithm's handling of imaginary
frequencies. Generating finite-temperature snapshots does not prove the parent
structure is dynamically stable.

The pypolymlp/SSCHA route remains `experimental` in this skill. The official
pages contain stale setup syntax, stale dependency ranges, and an unavailable
`--br` example. Before adding a recipe, inspect the exact 4.3.1 help and package
versions, establish energy-and-force extraction support for the selected
calculator, and validate train/test RMSE, configuration coverage, iteration
convergence, random-seed sensitivity, and target observables.

## Quasi-harmonic approximation

At least five ordered volume points are required:

```bash
phonopy-qha e-v.dat <thermal-properties-in-volume-order...>
phonopy-qha -p e-v.dat <thermal-properties-in-volume-order...>
phonopy-qha --eos birch_murnaghan -b e-v.dat
```

`e-v.dat` contains cell volume in Angstrom cubed and non-phonon energy in eV.
Every thermal-properties file must correspond one-to-one with those volumes and
use the same temperature range, step, normalization, electronic method, and
phonon acceptance policy. Supply one temperature point above the requested QHA
range because numerical differentiation consumes a point. Check that the
volume interval brackets equilibrium, EOS residuals and model sensitivity,
static-energy and phonon convergence, imaginary modes, and volume ordering.

Expected files include volume, thermal-expansion, Gibbs-energy, bulk-modulus,
heat-capacity, and fit products. Bind every claim to the exact output because
different heat-capacity routes do not have identical electronic-contribution
semantics. `--efe` is experimental. The official QHA page warns that a bulk
modulus obtained under nonzero `--pressure` is incorrect. QHA minimizes volume
for the supplied shape-versus-volume path; it is not a full anisotropic
free-energy minimization.

## Mode Gruneisen parameters

Prepare equilibrium, expanded, and contracted directories with consistent atom
mapping and accepted `FORCE_SETS` or `FORCE_CONSTANTS`:

```bash
phonopy-gruneisen orig plus minus \
  --dim="2 2 2" --pa=auto --mesh="20 20 20" \
  -c POSCAR-unitcell
phonopy-gruneisenplot -o gruneisen.pdf gruneisen.yaml
```

Use `--readfc` for force constants and an explicit calculator selector for a
non-VASP structure. Require the plus/minus volumes to bracket equilibrium,
consistent constrained-volume internal relaxation, identical calculator
settings, adequate volume step, and convergence of all three phonon models.
Inspect low-frequency and imaginary modes and divergence near Gamma.
`phonopy-gruneisen --band auto` is explicitly unsupported. Its official page
still lists a helper-local `--nac`; inspect exact native help before using that
flag rather than applying the removed main-CLI behavior by analogy.

## Documentation drift and failure semantics

The catalog records official-source conflicts instead of silently choosing a
tutorial line. Important cases are:

- old `phonopy -d/-f/-c` examples versus the v4 `phonopy-init` split;
- `--nac` text versus automatic v4 NAC and `--nonac`;
- tutorial `--symfc`, `--br`, and `phonopy-vasp-born --st` spellings absent
  from the pinned parser;
- `phonopy-proplot` typo versus the actual `phonopy-propplot` entrypoint;
- website examples with older banners;
- official interface navigation lagging the 17 parser-listed calculators;
- `projected_dos.dat` versus helper/default `partial_dos.dat` naming drift;
- pypolymlp dependency text that conflicts with the pinned package manifest.

Resolution order is: tag-pinned source/parser, same-version migration and
changelog, same-version command reference, official tutorial, then unversioned
prose. A successful exit code is never sufficient. Require the expected
artifact to be new or intentionally replaced, nonempty, parseable, shaped as
expected, and bound to source hashes. Preserve stdout/stderr because some
helpers have unusual exit behavior. Treat missing dependencies, parser errors,
YAML ancestry mismatch, atom/order mismatch, incomplete force series, NaN/Inf,
drift, imaginary modes, and an unconverged observable as distinct findings.

## Official sources used

- Changelog: <https://phonopy.github.io/phonopy/changelog.html>
- v4.3.1 release/tag: <https://github.com/phonopy/phonopy/releases/tag/v4.3.1>
- v4.3.1 package manifest: <https://github.com/phonopy/phonopy/blob/v4.3.1/pyproject.toml>
- Installation: <https://phonopy.github.io/phonopy/install.html>
- v4 migration: <https://phonopy.github.io/phonopy/migration-v4.html>
- `phonopy` and `phonopy-init`: <https://phonopy.github.io/phonopy/phonopy.html> and <https://phonopy.github.io/phonopy/phonopy-init.html>
- Workflow, options, examples, inputs, outputs, interfaces: <https://phonopy.github.io/phonopy/workflow.html>, <https://phonopy.github.io/phonopy/command-options.html>, <https://phonopy.github.io/phonopy/examples.html>, <https://phonopy.github.io/phonopy/input-files.html>, <https://phonopy.github.io/phonopy/output-files.html>, <https://phonopy.github.io/phonopy/interfaces.html>
- Auxiliary tools: <https://phonopy.github.io/phonopy/auxiliary-tools.html>
- QHA and Gruneisen: <https://phonopy.github.io/phonopy/qha.html> and <https://phonopy.github.io/phonopy/gruneisen.html>
- Random displacements and MLP/SSCHA: <https://phonopy.github.io/phonopy/random-displacements.html> and <https://phonopy.github.io/phonopy/mlp-sscha.html>
