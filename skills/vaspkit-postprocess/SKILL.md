---
name: vaspkit-postprocess
description: Discover, plan, call, and audit version-matched VASPKIT preprocessing and postprocessing tasks using the official 1.5 task catalog, actual interactive/CLI/stdin invocation modes, task-specific VASP inputs and outputs, environment configuration, documentation-conflict stops, and explicit native-validation state. Use for VASPKIT input generation, structure and symmetry tools, k paths, DOS/PDOS, conventional or hybrid bands, charge and potential grids, work functions, optical and MD analysis, semiconductor utilities, or when deciding what a VASPKIT task id does and whether it is safe to automate.
---

# VASPKIT Postprocess

Treat this as a manual-grounded candidate, not as an installed or executed
VASPKIT capability. The repository maintainer machine had no `vaspkit` command
in `PATH` on 2026-07-18. Preserve three separate statements:

1. the official feature page lists a task;
2. an official tutorial establishes a concrete recipe;
3. an exact binary/version was actually run and its output checked.

Never promote statement 1 or 2 into statement 3.

## Route the request

First search the pinned official catalog instead of guessing a menu number:

```text
python3 scripts/vaspkit_catalog.py categories
python3 scripts/vaspkit_catalog.py search "projected DOS"
python3 scripts/vaspkit_catalog.py show 115
python3 scripts/vaspkit_catalog.py plan 115
```

The catalog contains 174 task ids in 25 feature-page families and records four
additional top-level-only families. Read
[official-task-catalog.json](references/official-task-catalog.json) for the
complete map and [calling-and-recipes.md](references/calling-and-recipes.md) for
actual calls, inputs, outputs, checks, and scientific limits. Read
[practical-workflows.md](references/practical-workflows.md) before planning
input/structure generation, Fermi surfaces, work functions, optical/TDM, or MD;
it separates official task facts from operational heuristics and supplies the
parent-run and observable acceptance gates.

Use these high-level routes:

| User goal | Start with |
|---|---|
| INCAR, KPOINTS, POTCAR, CIF/POSCAR | 101–109; task 102 has an official flag/stdin recipe |
| Elasticity or equation of state | 200–205 |
| 1D/2D/bulk k path | 301–303, then independently check primitive cell and path |
| Structure edits, slabs, defects, symmetry | 400–419, 601–609, 800–827, 920–929 |
| TDOS/PDOS | 111–126; high-use recipes cover 111–115 |
| Conventional bands | 211–216; 211–214 have tutorial-grounded recipes |
| Hybrid bands | 250–257; 251/252 have tutorial-grounded recipes |
| 3D bands, Fermi surface, unfolding | 231–233, 261–267, 281–285 |
| Charge, spin, potential, work function | 310–329, 420–430 |
| Catalysis and thermochemistry | 501–509 |
| Wave function, magnetic, spin, transport | 511–516, 621, 651–653, 681–682 |
| Optical response | 710–719; exact binary inspection is mandatory because official pages conflict |
| MD analysis | 721–737 |
| Gap, effective mass, 2D band alignment | 911–917, 927 |

Task 109, 604, 710–713, 722, and 926 have conflicting labels across current
official pages. In particular, the feature page calls 722 FFT-MSD while the
tutorial calls it RDF. Stop batch planning for these ids until the installed
binary banner, menu label, help, prompts, and outputs are captured.

## Check the actual environment

```text
python3 scripts/vaspkit_catalog.py probe
command -v vaspkit
vaspkit -help
uname -sm
```

If no executable resolves, return `TOOL_UNAVAILABLE` for native execution. You
may still return a documentation plan, but label it `native_validation:
not_run`.

If an executable resolves, record its banner, version, platform/architecture,
SHA-256, official package URL, and usage-agreement review date. Review
`~/.vaspkit` without exposing private paths. In particular, check potential
paths/type, `RECOMMENDED_POTCAR`, `SET_FERMI_ENERGY_ZERO`, overwrite mode,
Python path, and plotting settings. Never commit VASPKIT binaries, licensed
`POTCAR` data, private calculation trees, or host-specific configuration.

## Select an invocation mode

The official tutorial documents five modes for task 102:

```text
vaspkit
vaspkit -task 102 -kpr 0.04
printf '102\n2\n0.04\n' | vaspkit
{ printf '%s\n' 102; printf '%s\n' 2; printf '%s\n' 0.04; } | vaspkit
vaspkit < cmd.in
```

It also shows `vaspkit -task 102 -file POSCAR -kpr 0.04`. These examples prove
only that task 102 has documented flag/stdin routes; the official tutorial says
some functions do not implement command-line flags. Use interactive mode to
discover an unpinned dialogue. Prefer a reviewed `cmd.in` plus captured
stdout/stderr for reproducible batch work:

```text
vaspkit < cmd.in > vaspkit.stdout 2> vaspkit.stderr
```

Do not copy `0.04` into a campaign as a convergence result and do not scrape a
fixed stdout line number.

## Validate the VASP parent before VASPKIT

Call `vasp-rigorous-calculations` for the parent VASP run. Require the exact
files, task semantics, completion, spin/SOC mode, structure identity, units,
energy reference, and observable-specific convergence. VASPKIT cannot repair an
incomplete or scientifically unsuitable VASP calculation.

Work on a scratch copy. Inventory and hash source files before launch, then
record files created or modified after launch. A generated plot is optional
presentation output, not a calculation-completion signal.

## Use the established recipes

Read the corresponding section in
[calling-and-recipes.md](references/calling-and-recipes.md) before producing
stdin:

- **102:** `POSCAR` → `KPOINTS`; mesh and centering still need convergence.
- **301–303:** `POSCAR` → `PRIMCELL.vasp`, `KPATH.in`,
  `HIGH_SYMMETRY_POINTS`; check SeeK-path and site mapping.
- **111–115:** accepted DOS calculation → TDOS/PDOS tables; preserve `LORBIT`,
  selector, spin convention, energy grid, normalization, and Fermi shift.
- **211:** matching `INCAR`, `DOSCAR`, `EIGENVAL`, `POSCAR`, `KPOINTS` plus
  stdin `211,0` → `BAND.dat`, `BAND_REFORMATTED.dat`, `KLINES.dat`,
  `KLABELS`, `BAND_GAP` and optional `band.png`.
- **212–216:** add projection-bearing `PROCAR` and exact atom/orbital selectors.
- **251/252:** build a weighted mesh plus zero-weight path from `KPATH.in`,
  run accepted hybrid VASP, then extract with stdin `252,0`.
- **261/262:** generate a converged dense primitive-cell mesh, run accepted
  VASP, then extract `FERMISURFACE.bxsf`; tasks 263–267 remain catalog-only
  until an exact-version dialogue is captured.
- **311–314:** derive charge/spin/difference grids; subtraction requires
  identical cell, grid, coordinates, ordering, and calculation convention.
- **426/427:** `LOCPOT` → planar/macroscopic averages; work functions require a
  matching Fermi level and a converged vacuum plateau.
- **503:** `INCAR`, `DOSCAR`, `POSCAR` → `D_BAND_CENTER`; record integration
  window and unoccupied-band convergence.
- **710–713:** exact-version inspection first; the tutorial's 711 route reads
  `vasprun.xml` when `REAL.in` and `IMAG.in` are absent, while its 712/713 TDM
  routes read matching `WAVECAR` and use a different menu map from the feature
  page.
- **721–737:** only task 721 has a pinned public output recipe
  (`POSCAR.ref` plus VASP MD output → `MSD.dat` and
  `ATOM_DISPLACEMENT.dat`). Treat 722 as a documentation conflict and the
  remaining MD prompt/output surfaces as catalog-only; validate periodic
  unwrapping, timestep, equilibration, selection, statistics, and fit/transform
  windows for the requested observable.
- **911/912:** gap/effective-mass workflows; prove extrema sampling and stable
  parabolic fits. Task 912 is documented as experimental.
- **923/927:** standardize a 2D cell and align band edges to vacuum; preserve
  atom mapping, slab side, dipole treatment, plateau, and energy reference.

For a task whose catalog record has no recipe, return
`VASPKIT_RECIPE_NOT_ESTABLISHED` and request an interactive transcript from the
exact version. Do not synthesize prompts from neighboring task ids.

## Audit native completion

Only state that a VASPKIT task completed when all are true:

1. executable identity and banner match the recorded version/platform;
2. argv or every stdin token is retained;
3. all required source files belong to the accepted parent run;
4. prompt/completion sentinels match the exact task and no fatal output appears;
5. expected outputs are newly created or intentionally replaced, nonempty,
   parseable, and hashed;
6. units, spin, atom/k-point mapping, and energy reference are explicit;
7. a separate scientific check passes for the requested observable.

For the narrow synthetic task-211/252 band-table path, the existing guard can
audit source records, a version-pinned transcript, and `BAND.dat`/`KLABELS`:

```text
python3 scripts/vaspkit_guard.py audit-source --source source.json
python3 scripts/vaspkit_guard.py plan-menu --source source.json --profile vaspkit-1.5.0-macos-intel --task 211
python3 scripts/vaspkit_guard.py audit-transcript --transcript transcript.txt --profile vaspkit-1.5.0-macos-intel --task 211
python3 scripts/vaspkit_guard.py parse-bands --source source.json --transcript transcript.txt --band BAND.dat --klabels KLABELS
```

That guard never launches VASPKIT and its synthetic pass does not validate a
native binary. It is not a substitute for the task catalog or recipes.

## Scientific limits

VASPKIT can prepare files, extract tables, transform grids, and make figures.
It does not by itself establish VASP completion, numerical convergence, a
correct k path, a global band gap, unique orbital/bond interpretation, vacuum
convergence, a valid MD fit, or a defensible materials conclusion. The official
tutorial also warns that its examples are guidance rather than certified
scientific prescriptions.

Use [official-sources.yaml](references/official-sources.yaml) for source
provenance, [task-recipes.json](references/task-recipes.json) for
machine-readable recipe state, [version-matrix.yaml](references/version-matrix.yaml)
for current binary profiles, and
[environment-and-license.md](references/environment-and-license.md) for
installation and licensing boundaries.
