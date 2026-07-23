# VASPKIT calling guide and task recipes

## Evidence status

This guide was checked against the official VASPKIT 1.5 website, the official
documentation source at commit `383a7103505b5b9436dedbf04df42ebb6e248638`,
and the 2025 Nature Protocols paper and companion example repository. The
maintainer machine did not have a `vaspkit` executable in `PATH` on
2026-07-18. Every recipe below is therefore one of:

- **official-recipe**: the invocation, prompts, inputs, or outputs are shown by
  an official tutorial;
- **official-catalog-only**: the task exists in the feature list, but this
  repository has not established a prompt sequence;
- **native-not-run**: no claim is made that the installed binary accepts the
  sequence or reproduces the output.

Do not silently turn an official-catalog-only task into a batch command. Open
the exact installed version interactively, capture its menu, and add a
version-specific recipe first.

## 1. Preflight the actual installation

Run these read-only checks before planning a task:

```bash
command -v vaspkit
vaspkit -help
uname -sm
```

If `command -v` is empty, stop with `TOOL_UNAVAILABLE`. If it resolves, record:

- the resolved executable path without committing private host paths;
- the VASPKIT banner/version, platform, architecture, and executable SHA-256;
- the official package/release URL and the usage-agreement review date;
- whether `~/.vaspkit` exists and which relevant settings are active;
- the VASP parent directory, task id, stdin record, stdout/stderr record,
  pre-existing files, and files created or changed by VASPKIT.

Do not run a first trial in the only copy of a calculation. Use a private
scratch copy and exclude licensed `POTCAR` content and unpublished results from
Git. A task menu number is not a version identity.

The official installation guide lists Python 3, NumPy, SciPy, and Matplotlib as
plotting/runtime dependencies and uses `~/.vaspkit` for configuration. Important
keys shown by the official guide include:

| Setting | Why it changes behavior |
|---|---|
| `VASP5` | Chooses VASP 5 versus legacy VASP 4 conventions. |
| `LDA_PATH`, `PBE_PATH`, `GGA_PATH` | Locate licensed potential libraries; never commit their contents or private paths. |
| `POTCAR_TYPE`, `GW_POTCAR`, `RECOMMENDED_POTCAR` | Select the potential family and recommendation policy. Verify compatibility with the calculation. |
| `SET_FERMI_ENERGY_ZERO` | Controls whether electronic energies are shifted so the selected Fermi level is zero. Record this in every dataset and figure. |
| `MINI_INCAR`, `USER_DEFINED_INCAR`, `SET_INCAR_WRITE_MODE` | Change template content and overwrite/append/backup behavior. |
| `PYTHON_BIN`, `PLOT_MATPLOTLIB` | Control automatic plotting. A missing plot is not proof the numerical task failed. |
| `VASPKIT_UTILITIES_PATH`, `ADVANCED_USER` | Enable local utilities; treat them as separate, user-controlled code. |

Before tasks that create `POTCAR`, explicitly verify the configured functional,
element order, potential label, and VASP license boundary. Never infer a
scientifically suitable potential from `RECOMMENDED_POTCAR=.TRUE.`.

## 2. The five official calling modes

The official quick-start tutorial documents at least five ways to run task 102.
Use the exact binary help because command-line flags are implemented for only a
subset of tasks.

### Interactive menu

```bash
vaspkit
```

Enter a top-level category or a full task id after the prompt. Interactive mode
is the safest discovery route when the prompt sequence has not been pinned.

### Direct task flags

```bash
vaspkit -task 102 -kpr 0.04
vaspkit -task 102 -file POSCAR -kpr 0.04
```

These are official task-102 examples. `0.04` is an example reciprocal-space
resolution, not an accepted convergence value. Do not assume another task
supports analogous flags merely because `-task` accepts its id.

### Standard-input pipeline

Prefer portable `printf` for a known prompt sequence:

```bash
printf '102\n2\n0.04\n' | vaspkit
```

The tokens mean task `102`, Gamma scheme `2`, and resolution `0.04` in the
official example. Confirm the installed prompt order before using this in
production.

### Grouped standard input

```bash
{ printf '%s\n' 102; printf '%s\n' 2; printf '%s\n' 0.04; } | vaspkit
```

This is equivalent to the grouped-input mode in the official tutorial and is
useful when values are generated separately.

### Input file

Create a reviewable `cmd.in`:

```text
102
2
0.04
```

Then run:

```bash
vaspkit < cmd.in
```

For traceability, retain `cmd.in` and capture output separately:

```bash
vaspkit < cmd.in > vaspkit.stdout 2> vaspkit.stderr
```

Do not scrape a fixed stdout line number such as `sed -n '40p'`; banner and
prompt changes make that fragile. Prefer a named result file or a parser that
checks semantic sentinels and the exact version.

## 3. Find the right task before invoking it

The official feature page contains 174 task ids in 25 enumerated families. Four
additional top-level families (`44`, `74`, `84`, `95`) appear in the 1.5 main
menu but have no child-task list on that feature-page snapshot. Search the
repository catalog:

```bash
python3 scripts/vaspkit_catalog.py categories
python3 scripts/vaspkit_catalog.py list --category 21
python3 scripts/vaspkit_catalog.py search 'projected band'
python3 scripts/vaspkit_catalog.py show 211
python3 scripts/vaspkit_catalog.py plan 211
```

`official-task-catalog.json` is a discovery index, not a menu transcript.
Tasks 109, 604, 710–713, 722, and 926 have conflicts between official pages in
the current snapshot. For task 722, the feature page says FFT-based MSD while
the tutorial prose says RDF. The catalog CLI must return the conflict and
require exact-binary inspection rather than choosing a meaning.

## 4. Practical recipes

### Task 102 — SCF KPOINTS generation

**Status:** official-recipe; native-not-run.

**Before:** place the intended `POSCAR` in a clean work directory. Decide the
mesh centering from the crystal and calculation, not from the example alone.

**Documented calls:**

```bash
vaspkit -task 102 -file POSCAR -kpr 0.04
printf '102\n2\n0.04\n' | vaspkit
```

**Creates:** `KPOINTS`.

**Check:** parse the written mesh, centering, reciprocal resolution comment,
symmetry suitability, and convergence against the target observable. Do not
replace a converged project mesh with `0.04` just because it appears in the
tutorial.

### Tasks 301, 302, 303 — 1D, 2D, and bulk k paths

**Status:** official-recipe for the documented 2D/bulk workflow;
native-not-run.

**Before:** provide `POSCAR`. Standardize and inspect the structure first. The
official 2D recipe assumes vacuum along `c` and centers the layer; it uses task
923 for a 2D standardization example. The official bulk workflow points to task
602 for a primitive cell.

**Call:** use `301`, `302`, or `303` interactively, or a one-token input file
only after the exact binary prompt is confirmed:

```bash
printf '302\n' | vaspkit
```

**Creates in the documented workflow:** `PRIMCELL.vasp`, `KPATH.in`, and
`HIGH_SYMMETRY_POINTS`.

**Check:** compare `PRIMCELL.vasp` atom count, lattice, species, site mapping,
and dimensionality with the intended structure. The official tutorial itself
warns that VASPKIT does not guarantee the path is correct and recommends
checking high-symmetry points with SeeK-path. A plausible path is not evidence
that the scientific path convention matches a paper or previous campaign.

### Task 211 — conventional band postprocessing

**Status:** official-recipe; synthetic transcript/parser tested;
native-not-run.

**Before:** require an accepted VASP band calculation and the matching
`INCAR`, `DOSCAR`, `EIGENVAL`, `POSCAR`, and line-mode `KPOINTS`. K-point labels
must be present in `KPOINTS` if meaningful labels are expected.

Create:

```text
211
0
```

and run:

```bash
vaspkit < cmd.in > vaspkit.stdout 2> vaspkit.stderr
```

The second token accepts the documented default plotting setting. The official
tutorial says the default route shifts the Fermi energy to zero; verify
`SET_FERMI_ENERGY_ZERO` and preserve the actual reference.

**Documented outputs:** `BAND.dat`, `BAND_REFORMATTED.dat`, `KLINES.dat`,
`KLABELS`, `BAND_GAP`, and optionally `band.png` when plotting is configured.

**Interpretation:** the first column of `BAND_REFORMATTED.dat` is k-path length
in inverse angstrom and later columns are band energies. `KLABELS` maps
high-symmetry labels to plotting coordinates. Undefined labels mean the source
path labels were missing or unrecognized. `BAND_GAP` is an extraction over the
sampled data; it does not prove the global gap, convergence, correct spin/SOC
semantics, or a physically meaningful Fermi reference.

### Tasks 212–216 — projected conventional bands

**Status:** official-recipe for 212–214; catalog-only for selector/output
details not shown here; native-not-run.

**Before:** all task-211 inputs plus `PROCAR`. Generate projection data with an
appropriate `LORBIT`; the official tutorial explicitly calls for `LORBIT=10` or
`11`. Keep the VASP version, PAW projection convention, spin/SOC mode, atom
mapping, and orbital basis.

Task 212 official example:

```text
212
1-2
```

**Documented outputs:** task 212 writes `SELECTED_ATOM_LIST`, per-selected-atom
`PBAND_A*.dat`, `KLINES.dat`, and `KLABELS`; task 214 writes
`PBAND_SUM.dat`. Task 213 produces element projections. Task 215 is listed as
element-weight bands and 216 as an atom/orbital sum.

**Check:** selector meaning, atom numbering, element order, projection columns,
spin channels, and whether weights sum as expected. Projection weights are
basis-dependent descriptors, not unique oxidation states or chemical bonds.

### Tasks 251–257 — hybrid-functional band workflow

**Status:** official-recipe for 251/252; native-not-run.

1. Obtain `PRIMCELL.vasp`, `KPATH.in`, and `HIGH_SYMMETRY_POINTS` with task 302
   or 303 and independently check them.
2. Place the calculation structure as `POSCAR` and the checked path as
   `KPATH.in`.
3. Run task 251. The official prompt requests mesh scheme, weighted SCF mesh
   resolution, then zero-weight path resolution:

```text
251
2
0.05
0.05
```

   This sequence reproduces the tutorial example only; it does not establish
   convergence. Task 251 creates a `KPOINTS` containing symmetry-weighted SCF
   points and zero-weight path points.
4. Run and accept the hybrid VASP calculation. Preserve `INCAR`, `DOSCAR`,
   `EIGENVAL`, `POSCAR`, `KPOINTS`, and the original `KPATH.in`.
5. For task 252, use:

```text
252
0
```

**Documented task-252 outputs:** `BAND.dat`, `BAND_REFORMATTED.dat`,
`KLINES.dat`, `KLABELS`, `BAND_GAP`, and optionally `band.png`.

Tasks 253–257 provide projected hybrid variants analogous to 212–216 and need
projection-bearing VASP output. Do not assume their prompt sequences from the
conventional tasks without an exact-version transcript.

### Tasks 261–267 — Fermi surface

**Status:** official-recipe for the 261/262 bulk route; catalog-only for
263–267; native-not-run.

The official bulk tutorial uses an optimized primitive-cell `POSCAR`, task 261
to write a dense reciprocal-space `KPOINTS`, an accepted VASP calculation, and
then task 262. The task-261 resolution is in `2*pi/angstrom`; the tutorial's
`0.008` is only an example. Task 262 reads matching `INCAR`, `POSCAR`, `DOSCAR`,
and `EIGENVAL` and writes `FERMISURFACE.bxsf`.

Tasks 263–267 advertise FermiSurfer, projected, summed-projection, and 2D
variants, but the pinned public tutorial does not establish their prompts or
output names. Discover them interactively on the exact version.

Check primitive-cell/site mapping, dense-mesh convergence of topology and
extremal dimensions, Fermi-reference sensitivity, spin/SOC semantics,
reciprocal units, symmetry expansion, band indices, and representative parent
eigenvalues. Viewer band selection and a plausible surface are not scientific
acceptance. See [practical-workflows.md](practical-workflows.md) for the full
gate.

### Tasks 111–115 — DOS and selected PDOS

**Status:** official-recipe; native-not-run.

**Before:** accepted VASP DOS output, normally including `INCAR`, `POSCAR`,
`DOSCAR`, and `OUTCAR` for the documented Fermi shift route. For PDOS, the
official tutorial requires `LORBIT=10` or `11` during VASP: `10` gives
angular-momentum decomposition and `11` gives magnetic-quantum-number
decomposition in the documented route.

| Task | Selection | Documented output |
|---|---|---|
| 111 | none | `TDOS.dat`, `ITDOS.dat`; both spin channels may share one table |
| 112 | atom indices/elements | `SELECTED_ATOM_LIST`, per-atom `PDOS_A*_UP/DW.dat` and integrated counterparts |
| 113 | none | one PDOS file per element, with spin-specific names when applicable |
| 114 | atom indices/elements | `SELECTED_ATOM_LIST`, summed `PDOS_SUM_UP/DW.dat` and integrated counterparts |
| 115 | repeated atom/element and orbital selections | `PDOS_USER.dat`; the tutorial shows selectors such as `s`, `p`, `d`, resolved orbitals, or `all` |

Use interactive mode for 112–115 until the complete selector dialogue is
captured for the exact version. Record whether energies were shifted by
`SET_FERMI_ENERGY_ZERO`. Check DOS grid, smearing/tetrahedron method, energy
window, normalization, spin sign convention, atom/orbital selector, and electron
count where meaningful. A smooth or attractive PDOS curve is not a convergence
test.

### Task 503 — d-band center

**Status:** official-recipe; documented as experimental; native-not-run.

**Before:** matching `INCAR`, `DOSCAR`, and `POSCAR`, with enough unoccupied
bands and a justified integration window.

Official dialogue shape:

```text
503
y
-11.8 0
```

The energy window is an example, not a universal choice. The task writes
`D_BAND_CENTER` and reports atom-resolved and total values referenced to the
selected Fermi-zero convention.

**Check:** energy window, Fermi reference, DOS normalization, atom selection,
spin handling, and `NBANDS`. The official tutorial warns that the result is
sensitive to the number of unoccupied bands and that trends are more reliable
than absolute values. Do not compare values produced with different windows or
electronic setups as if they were commensurate.

### Tasks 311–314 — charge and spin grids

**Status:** official-recipe; native-not-run.

- `311` reads charge-grid data and writes `CHARGE.vasp`.
- `312` writes `SPIN.vasp`.
- `313` writes `SPIN_UP.vasp` and `SPIN_DW.vasp`.
- `314` subtracts two or more explicitly named grid files and writes
  `CHGDIFF.vasp`.

Official task-314 example:

```text
314
./CHGCAR ./fragment-a/CHGCAR ./fragment-b/CHGCAR
```

This represents the first grid minus the following grids. The official
adsorption example keeps fragment coordinates from the optimized combined
structure rather than relaxing fragments independently.

**Check before subtraction:** identical cell vectors, grid dimensions, atom
coordinates, atom ordering, charge convention, calculation settings, and
physical subtraction definition. A file that VESTA can display is not proof
that the subtraction is meaningful.

### Tasks 426 and 427 — planar and macroscopic potential

**Status:** official-recipe; native-not-run.

**Before:** matching `LOCPOT`, converged slab/vacuum, and `OUTCAR` when a work
function is needed. Know whether the grid contains total local potential
(`LVTOT`) or ionic-plus-Hartree electrostatic potential (`LVHAR`); the official
work-function example uses `LVHAR=.TRUE.`.

For a slab normal to z:

```text
426
3
```

Task 426 writes `POTPAVG.dat`; its columns are distance in angstrom and averaged
potential in eV for `LOCPOT`. Determine a vacuum plateau and combine it with the
Fermi energy from the same VASP calculation:

```text
work function = vacuum level - Fermi level
```

Task 427 additionally requests averaging direction, an averaging period close
to but below the repeat-layer distance, and an iteration count. The documented
outputs are `PLANAR_AVERAGE.dat` and `MACROSCOPIC_AVERAGE.dat`.

**Check:** vacuum-thickness convergence, both slab sides, dipole correction and
asymmetry, plateau selection, potential definition, surface normal, averaging
period, and common energy reference. Never report the tutorial's numerical
example as a default.

### Task 711 — bulk linear optical spectra

**Status:** official-recipe, but task numbering conflicts across official
pages; native-not-run.

The official 1.5 tutorial says:

```bash
vaspkit -task 711
```

or interactively:

```text
711
1
```

where the second token selects eV rather than nm or THz. If `REAL.in` and
`IMAG.in` are absent, the tutorial says VASPKIT 1.00+ reads the dielectric
function from `vasprun.xml`. It then writes optical-property tables.

**Stop condition:** the feature page distinguishes task 710 for 2D spectra and
711 for bulk, while the tutorial menu has changed across versions and includes
task 712 not present in the feature catalog. Inspect the installed menu/banner
before automation. The tutorial warns its 711 route is not suitable for
low-dimensional materials.

**Check:** VASP optical prerequisites, tensor components, polarization,
broadening, frequency/energy units, sum rules, convergence in bands/k points,
and whether local-field/excitonic physics matches the requested claim.

### Tasks 721–728 — molecular-dynamics analysis

**Status:** official-recipe for 721 and catalog entries for the rest;
native-not-run.

Task 721 requires a reference structure named `POSCAR.ref` and VASP MD results;
the official tutorial says it writes `MSD.dat` with directional displacement,
MSD, and RMSD columns.

The tutorial also states that `ATOM_DISPLACEMENT.dat` contains per-atom
displacement/RMSD information. Related feature-catalog tasks are:

- `722`: FFT-based MSD;
- `723`: diffusion coefficient and ionic mobility from `MSD.dat`;
- `725`: pair correlation from `PCDAT`;
- `726`: element-selected radial distribution;
- `727`: velocity autocorrelation;
- `728`: vibrational DOS from the velocity autocorrelation.

Task 722 is documentation-conflicted: the feature catalog labels it FFT-based
MSD, while the tutorial prose labels 722 as RDF. Do not run 722 from either
label without capturing the exact binary menu and prompt. Tasks 730/731 and
736/737 additionally advertise bond-length/angle distributions and selected
trajectory exports but remain catalog-only here.

For any MD task, confirm exact trajectory source, atom selection, timestep,
temperature ensemble, equilibration discard, periodic-boundary unwrapping,
origin averaging, fitting window, and units. A linear fit to a short or
non-diffusive MSD segment is not a valid diffusion coefficient. Use the
observable-specific acceptance gates in
[practical-workflows.md](practical-workflows.md).

### Tasks 911 and 912 — gap and effective mass

**Status:** official-recipe; task 912 is experimental; native-not-run.

Task 911 extracts the band gap from the current VASP result. Prefer its named
output or a semantic parser; do not scrape a fixed stdout line.

Task 912 has two stages controlled by `VPKIT.in`: preprocess a local k-point
sampling around declared band extrema, run the corresponding VASP calculation,
then postprocess a quadratic fit. The official tutorial explicitly restricts
its illustrated workflow to a neutral, non-magnetic semiconductor.

**Check:** global versus sampled extrema, spin/SOC, degeneracy, exact k-point
direction, reciprocal units, fit radius and number of points, parabolicity,
band crossings, and numerical convergence. Mark an effective mass invalid when
the fitted band is not locally quadratic over a stable window.

### Tasks 923 and 927 — 2D standardization and vacuum-referenced band edges

**Status:** official-recipe; native-not-run.

Task 923 reads `POSCAR` and writes `POSCAR_NEW` in the documented 2D example,
placing vacuum along z and centering/standardizing the layer. Inspect the atom
mapping, cell, area, vacuum, and fractional coordinates before replacing any
source structure.

Task 927 combines 2D band edges with a vacuum reference. Require an accepted
band calculation and converged planar potential from the same structure and
electronic setup. Report the chosen vacuum plateau, Fermi/band-edge reference,
surface side, dipole treatment, and uncertainty. The feature page labels task
926 as stacking-dependent potential energy, while the tutorial menu labels 926
as 2D elastic constants; inspect exact-version menus for 926.

### Tasks 400, 401, and 601–604 — structure and symmetry utilities

**Status:** official-recipe for 400/401/601/602 examples; version-sensitive
for 604; native-not-run.

- Task 400 reads a 3x3 integer transformation, from prompts or documented
  `TRANSMAT.in`, and writes a transformed structure such as
  `SUPERCELL.vasp`.
- Task 401 asks for a structure source and integer repeats along a, b, and c.
- Task 601 reports crystal symmetry from `POSCAR`.
- Task 602 creates a primitive-cell representation in the documented workflow.
- Task 604 has conflicting meanings in official feature and tutorial pages;
  never batch it until the installed menu has been captured.

After any structural operation, compare lattice determinant, atom count,
composition, Cartesian geometry, periodicity, site mapping, and intended
selective-dynamics flags. Symmetry depends on tolerance and geometry; a
high-symmetry label from an unrelaxed or numerically distorted structure is not
automatically the correct model.

## 5. Completion and interpretation gates

For every native run, require all of the following before saying “VASPKIT
completed”:

1. exact executable identity and banner captured;
2. exact task id and stdin/argv retained;
3. required source files existed before launch and belonged to one accepted
   parent calculation;
4. stdout/stderr contained no fatal condition and the expected task-specific
   completion sentinels appeared in order;
5. expected outputs were newly created or intentionally replaced, nonempty,
   parseable, and hashed;
6. units, spin convention, atom/k-point mapping, and energy reference were
   explicit;
7. the result passed an observable-specific scientific check independent of
   VASPKIT.

Passing the first six establishes an auditable tool run. Only the seventh can
support a scientific interpretation, and it must still inherit the convergence
and validity limits of the parent VASP calculation.

## 6. Official sources used

- VASPKIT overview and 1.5 top-level menu:
  <https://vaspkit.com/>
- Complete feature-page task list:
  <https://vaspkit.com/features.html>
- Quick start and task tutorials:
  <https://vaspkit.com/tutorials.html>
- Installation, dependencies, configuration, and usage agreement:
  <https://vaspkit.com/installation.html>
- Release notes:
  <https://vaspkit.com/changelog.html>
- 2025 Nature Protocols guide:
  <https://doi.org/10.1038/s41596-025-01160-w>
- Official companion examples:
  <https://github.com/vaspkit/VASPKIT_NatureProtocols>

The official tutorial contains its own warning that examples are guidance and
are not guaranteed to be scientifically certified. This Skill preserves that
boundary: official documentation supports what VASPKIT is documented to do,
not whether a specific calculation or interpretation is scientifically sound.
