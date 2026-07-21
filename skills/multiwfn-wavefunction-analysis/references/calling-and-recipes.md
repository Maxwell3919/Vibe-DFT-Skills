# Multiwfn calling and version-bound recipes

## Status and evidence layers

This guide is pinned to the official Multiwfn program update `2026.7.15` and
the official manual dated `2026.7.10`. The source review date is 2026-07-22.
The current Darwin arm64 host had neither `Multiwfn` nor `multiwfn` in `PATH`,
and no Python distribution named `multiwfn`; no banner, help, menu, example, or
scientific calculation was executed. The native state is therefore
`native-not-run`.

Keep four evidence layers separate:

1. `official-function-catalog.json` records the 29 main functions, manually
   indexed subfunctions, input families, and documented invocation forms.
2. `task-recipes.json` records only menu sequences actually stated in the
   pinned official manual. A function listing is not a recipe.
3. `multiwfn_catalog.py` searches those two files and emits a documentation
   plan. It never launches Multiwfn.
4. `multiwfn_guard.py` audits a narrow source/transcript/interchange-table
   contract. It is not a general Multiwfn launcher or scientific validator.

Use the catalog before constructing any menu stream:

```text
python3 scripts/multiwfn_catalog.py families
python3 scripts/multiwfn_catalog.py list --main
python3 scripts/multiwfn_catalog.py search "Hirshfeld-I"
python3 scripts/multiwfn_catalog.py show 20.11
python3 scripts/multiwfn_catalog.py plan igmh-interfragment
python3 scripts/multiwfn_catalog.py probe
```

`plan` returns exit `0` only for a documentation plan and always keeps
`execution_authorized: false`. If a menu feature is listed but has no exact
recipe, it returns exit `3` with `MULTIWFN_RECIPE_NOT_ESTABLISHED`.

## Environment and distribution boundary

The official download page publishes Windows and Linux distributions. For
Linux it distinguishes a full distribution and a noGUI distribution. The
noGUI build removes graphical-library requirements but cannot provide
graph-dependent functions. The official page does not publish an official
macOS build; it points to a user-maintained build and warns that its version may
lag or differ. Do not substitute that build for `2026.7.15` without recording
its source, build, banner, executable digest, platform, and regression evidence.

Before native use, record all of the following without committing private
paths or unpublished wavefunctions:

- official distribution page and reviewed license/citation terms;
- package and executable SHA-256, platform, architecture, and program banner;
- full versus noGUI identity and the exact update date shown by the program;
- `settings.ini` identity, its SHA-256, and any `Multiwfnpath` configuration;
- thread count and the host's physical-core choice;
- stack, shared-memory, and process limits relevant to the selected workload,
  including any `OMP_STACKSIZE` and `ulimit` changes;
- auxiliary executables or converters and the separate authorization for each;
- one complete stdin/stdout/stderr transcript in a fresh scratch directory.

The official manual warns that documented command-line arguments may not take
effect when `settings.ini` cannot be found. Treat a missing or unexpected
settings file as a configuration failure; do not assume that `-nt`, `-set`, or
other requested behavior was applied. Keep the actual settings file with the
private run manifest.

The manual documents `-nt`, `-uf`, `-silent`, and `-set`. Use only the exact
semantics of the pinned manual and exact program banner. Its explicit example
is:

```text
Multiwfn COCl2.fch -nt 36 -set /sob/tmp/settings.ini -silent
```

The filename, thread count, and settings path are examples, not defaults or
recommendations for another machine.

## Startup and input-stream forms

The official manual documents interactive startup and startup with a file:

```text
Multiwfn
Multiwfn <input-file>
```

With bare `Multiwfn`, provide the path at the input prompt. An empty response
may open a graphical file chooser, which is unsuitable for a traceable noGUI
or batch route. Supply an explicit path instead.

For a documented stdin sequence, store one token or response per line and
capture both output streams:

```text
Multiwfn <input-file> -silent < commands.in \
  > multiwfn.stdout 2> multiwfn.stderr
```

The manual also demonstrates shell echo/heredoc-style input. A checked-in or
campaign-recorded `commands.in` is usually easier to hash, review, and replay.
Do not create the stream from a submenu title or from a different program
version. The main-menu exit token is `q`, but add it only at a prompt that the
exact transcript proves is the main menu; `q` can mean something else inside a
selection submenu.

An input file is data, not proof of successful parsing. The transcript must
show the expected banner, loaded basename and format, atom/orbital/grid
summary, ordered prompts, selected method, and completion or explicit return.

## Input eligibility

Select a function only when the loaded format provides every required data
family. The catalog summarizes seven families:

| Input family | Representative formats | Available content | Hard boundary |
|---|---|---|---|
| Full wavefunction and basis | `.mwfn`, `.fch/.fchk`, Molden, `.gbw`, `.gms` | basis functions, GTFs, coordinates | direct `.chk`/`.gbw` routes may require configured converters; verify Molden and ECP semantics |
| GTF wavefunction | `.wfn`, `.wfx`, NBO plot sets | GTFs and coordinates | `.wfn/.wfx` do not carry basis-function identity or virtual orbitals |
| Structure only | `.pdb`, `.xyz`, `.cif`, POSCAR, QE/CP2K inputs and others | coordinates | no orbital, density, or grid analysis may be inferred |
| Coordinates and charges | `.chg`, `.pqr` | coordinates and assigned charges | no electronic wavefunction |
| Grid with structure | cube, CHGCAR/CHG, ELFCAR, LOCPOT | grid and coordinates | verify cell, units, ordering, periodic convention, and field identity |
| Grid only | `.vti`, `.grd`, `.dx` | grid | atom and wavefunction identity are absent |
| Special text | supported program outputs or plain text | task-specific | eligibility belongs to the selected spectrum/DOS/other parser |

Never rename an ineligible file to a supported suffix. For ECP calculations,
preserve the nuclear-charge/core-electron convention and any electron-density
function treatment required by the selected analysis. For orbital composition,
Mayer order, PDOS/OPDOS, and related basis-space analyses, require a
basis-function-bearing source rather than `.wfn`/`.wfx` alone.

## The 29 main functions

These are menu-family listings from the pinned manual, not unattended recipes:

| ID | Function family | ID | Function family |
|---:|---|---:|---|
| 0 | Structure, orbitals, and isosurfaces | 1 | Properties at a point |
| 2 | Topology | 3 | Property along a line |
| 4 | Property in a plane | 5 | Property in a spatial region |
| 6 | Check or modify wavefunction | 7 | Population and atomic charges |
| 8 | Orbital composition | 9 | Bond order |
| 10 | DOS, PES, and COHP | 11 | Vibrational/electronic/NMR spectra |
| 12 | Quantitative molecular surface | 13 | Grid-data processing |
| 14 | AdNDP | 15 | Fuzzy atomic-space analysis |
| 16 | Charge decomposition/orbital interaction | 17 | Basin analysis |
| 18 | Electron-excitation analysis | 19 | Orbital localization |
| 20 | Weak-interaction visualization | 21 | Energy decomposition |
| 22 | Conceptual DFT | 23 | ETS-NOCV |
| 24 | Hyperpolarizability | 25 | Delocalization and aromaticity |
| 100 | Other functions, part 1 | 200 | Other functions, part 2 |
| 300 | Other functions, part 3 |  |  |

Use `show <main>.<sub>` for an indexed submenu, for example `show 7.15`,
`show 13.20`, or `show 20.11`. The result has
`evidence: manual-index-listing-only`; do not turn its two menu numbers into a
complete input script without a recipe and prompt transcript.

## Version-bound recipes

### Orbital composition

The official manual's command-stream example loads `COCl2.fch` and uses:

```text
8
1
1
2
3
```

This is main function 8, Mulliken composition, followed by orbitals 1, 2, and
3 in the tutorial's prompt context. It requires basis-function-bearing data.
Record orbital numbering, alpha/beta or restricted convention, occupations,
method, basis, ECP, and atom/basis ordering. Mulliken contributions are
basis-sensitive; diffuse functions can make them unsuitable.

Catalog route:

```text
python3 scripts/multiwfn_catalog.py plan orbital-composition-mulliken
```

### ELF cube

The official input-stream example is:

```text
5
9
2
2
```

It enters spatial-region analysis, selects ELF, chooses the manual's grid
route, and writes the fixed filename `ELF.cub`. The tutorial's grid choice is
not convergence evidence. Use a new scratch directory; verify that the target
does not exist; hash the cube; check dimensions, origin, axes, units, atom
list, finite values, and physical plausibility; then repeat with refined grids
until the claimed quantity or isosurface is stable.

### Population and charge routes

The pinned manual tutorials state these prefixes:

| Analysis | Sequence | Required evidence and checks |
|---|---|---|
| Mulliken population | `7, 5, 1` | basis-bearing source; electron count, net charge, spin population, basis/atom order; diffuse-function warning |
| Hirshfeld charge | `7, 1, 1` | free-atom density route, grid/settings, raw and normalized sums, dipole, atom order |
| ADCH charge | `7, 11, 1` | underlying Hirshfeld route, normalized charge conservation, reproduced dipole error |
| Hirshfeld-I | `7, 15, 1` | atomic radial-density provenance, iteration threshold/convergence, charge sum, sensitivity |

These are interactive prefixes unless the exact binary transcript establishes
all later prompts, exports, filenames, and return tokens. The Hirshfeld tutorial
can offer a `.chg` export, but the prompt and filename must be captured before
batching. Do not let a Hirshfeld-I path invoke Gaussian or create atomic radial
data without separate authorization and exact provenance. No population
partition is a unique observable, oxidation state, or proof of bonding.

### Mayer and fuzzy bond orders

The official tutorial prefixes are:

```text
# Mayer
9
1

# fuzzy bond order
9
7
```

Mayer analysis requires basis-function-bearing data. An optional `y` response
can export `bndmat.txt`; do not append it until the exact prompt is recorded.
For Mayer, retain the basis, occupations, spin, threshold, atom order, and
matrix hash. For fuzzy bond order, retain the atomic-space partition,
integration grid, threshold, and numerical convergence. Both remain
wavefunction- and definition-dependent.

### AIM topology

The official tutorial follows this interactive GUI path:

```text
2
2
3
0
<close the GUI window>
8
0
```

It is not a noGUI or unattended recipe. Record critical-point search settings,
coordinates, types, duplicates, convergence, bond paths, and ECP/electron-density
treatment. Check expected and unexpected critical points and the relevant
Poincare-Hopf relation. That relation alone does not prove that every critical
point was found or chemically interpreted correctly.

### TDOS, PDOS, and OPDOS

The official TDOS tutorial begins with:

```text
10
0
```

It opens an interactive plot in the documented full build. Record the orbital
energy source, spin, energy reference/unit, occupations, degeneracy,
broadening, and plotted range. A smooth curve is not evidence that the parent
electronic structure, k sampling, or broadening is adequate.

The manual's N-phenylpyrrole PDOS/OPDOS example uses this exact example stream:

```text
10
-1
1
a 1-5
q
2
a 10-13,15,17
q
3
a 6-9,14,16,18-20
q
0
2
-1.1,-0.1,0.1
0
```

Its atom/basis selections and energy window are system-specific and must never
be copied to a different molecule. Review each fragment selection, basis
composition method, diffuse functions, spin, reference, and broadening. This
route is GUI-bound until a separately validated noninteractive export path is
established.

### IGMH

The official interfragment tutorial sequence is:

```text
20
11
2
1-12
13-25
2
3
```

The tutorial writes `sl2r.cub` and `dg_inter.cub` among task-dependent grid
outputs. Replace both atom ranges with reviewed fragments, never with inferred
contiguous groups. Converge the box and grid; preserve partition/settings and
cube hashes; verify cell/axes/units/atom order/finite values. Isovalue and color
choices are presentation parameters, and an IGMH isosurface does not uniquely
quantify interaction energy.

### Hole/electron cubes

The official excited-state workflow is represented by:

```text
18
1
<matching-excited-state-output>
2
1
3
10
11
```

It can produce `hole.cub` and `electron.cub`. The tutorial's state and grid
choices are examples. Require a mutually matching wavefunction and
excited-state output, method/parser compatibility, identical geometry and
basis, explicit state/spin numbering, normalized transition coefficients,
grid convergence, and integrated hole/electron population checks. Capture the
full export-menu transcript before treating this prefix as batch-ready.

## Noninteractive boundary

Only `orbital-composition-mulliken` and `elf-cube` are marked
`batch_ready: true` because the pinned manual explicitly gives their stdin
streams. Even those remain documentation plans on this host. All charge,
bond-order, topology, DOS, IGMH, and excitation recipes are either interactive
prefixes or GUI paths. They require an exact private transcript before an
execution adapter may feed them unattended.

For any future batch route:

1. work in an empty scratch directory containing reviewed copies or links with
   recorded identity;
2. reject existing fixed-name outputs;
3. record executable/settings/input/stdin hashes before launch;
4. capture stdout and stderr separately without truncation;
5. check banner, prompt order, chosen options, loaded file, and explicit return;
6. hash and parse every expected artifact, including zero-byte/unmodified checks;
7. leave the scientific claim ceiling at the selected observable's acceptance
   profile rather than at process exit zero.

## Failure semantics

| Observation | Required classification | Next action |
|---|---|---|
| `Multiwfn`/`multiwfn` does not resolve | `TOOL_UNAVAILABLE`; documentation-only | install/review separately or transfer the plan; never claim a native run |
| Banner/update date differs from `2026.7.15` | version/profile mismatch | select matching manual/catalog or capture and review a new profile |
| `settings.ini` is missing or unexpected | configuration failure | stop; locate and hash the intended settings; do not trust requested CLI options |
| Function is listed but no recipe exists | `MULTIWFN_RECIPE_NOT_ESTABLISHED` | capture complete prompts and failure behavior; do not guess menu tokens |
| noGUI build meets a graph/GUI step | incompatible execution mode | use the exact full distribution on a supported platform or choose a documented data-export route |
| Input family lacks basis, GTF, orbitals, grid, charges, or atoms required by the task | input-ineligible | obtain a semantically complete producer artifact; never infer missing content |
| Fixed output already exists | output collision | use a new scratch directory; never interpret a stale overwritten/unchanged artifact |
| Expected output absent, empty, unchanged, nonfinite, or structurally invalid | technical failure | retain transcript and diagnose the first missing prerequisite or prompt drift |
| EOF produces an Intel Fortran runtime message after a documented stream | ambiguous termination, not automatically success or failure | inspect prompt position, explicit exit, expected artifacts, and earlier fatal text; prefer a validated `q` return at the proven main menu |
| Program exits zero and produces a plot/table | process completion only | apply provenance, numerical, method-applicability, and scientific checks independently |

The manual notes EOF/runtime behavior in stream-driven use. Do not suppress
stderr globally or classify every trailing runtime message in isolation. A
partial transcript may have completed one artifact while leaving another
selection unfinished. Conversely, an output file can predate the run. Artifact
identity, modification, content validation, and ordered prompts decide the
technical state.

External converters, Gaussian calls, viewers, renderers, and postprocessing
programs are separate tools. Their availability, version, inputs, outputs,
license, side effects, and failure semantics require independent adapters; a
Multiwfn menu option does not authorize them.

## Scientific boundary

Multiwfn can compute many well-defined quantities from a supplied file, but it
cannot repair an unconverged or semantically incomplete parent calculation.
Always validate geometry, electronic state, method, basis/ECP, convergence,
producer export, atom/orbital mapping, units, and file hashes first. Then apply
observable-specific checks such as grid convergence, charge closure,
critical-point completeness, broadening sensitivity, or transition-density
normalization. Attractive surfaces, spectra, charge tables, and bond orders are
derived representations rather than self-validating chemical conclusions.

## Official sources used

- Official download, platform, version, terms, and package information:
  <http://sobereva.com/multiwfn/download.html>
- Official update history: <http://sobereva.com/multiwfn/update.html>
- Official manual dated 2026.7.10:
  <http://sobereva.com/multiwfn/misc/Multiwfn_manual_2026.7.10.pdf>
- Official quick start:
  <http://sobereva.com/multiwfn/misc/Multiwfn%20quick%20start.pdf>

The official pages are the authority for current distribution, license, and
citation requirements. This repository records URLs and review dates but does
not download a binary, accept terms, or redistribute official program files.
