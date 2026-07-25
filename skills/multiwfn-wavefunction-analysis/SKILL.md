---
name: multiwfn-wavefunction-analysis
description: Plan, document, and audit version-bound Multiwfn wavefunction, real-space, topology, population, orbital, bond-order, DOS/spectrum, weak-interaction, grid, and excitation analyses using the official 2026.7.10 manual, a searchable 2026.7.15 function catalog, exact documented menu recipes, fail-closed source/transcript gates, and explicit GUI/noGUI and scientific boundaries. Use when a user asks what Multiwfn function or input format applies, how to invoke it interactively or by stdin, what files and outputs a workflow needs, or whether a Multiwfn-derived result is traceable and supportable.
---

# Multiwfn Wavefunction Analysis

Read [the local official-manual cache route](references/manual-cache-route.md) before using the external official PDFs; keep those local and do not redistribute them.

Use this development Skill for maintenance and documentation planning only.
Do not route it as an active Skill and do not launch, download, install, or feed
Multiwfn unless a later task supplies separate authorization and an exact
validated execution adapter.

## Establish the evidence state

1. Pin the intended program banner/update date and platform. This source is
   reviewed against program `2026.7.15` and official manual `2026.7.10`.
2. Record the producer calculation, geometry, charge, multiplicity, spin,
   method, basis/ECP, convergence, export lineage, input basename, SHA-256, and
   bytes. A supported suffix is not proof of sufficient contents.
3. Classify the input with the seven families in
   [official-function-catalog.json](references/official-function-catalog.json).
4. Separate a main/subfunction listing from an established menu recipe. Never
   infer later prompts from a function number.
5. Keep this host's state as `native-not-run`: neither `Multiwfn` nor
   `multiwfn` resolved on Darwin arm64 and no banner/help/example was run.

## Query before planning

Use the standard-library-only catalog helper:

```text
python3 scripts/multiwfn_catalog.py families
python3 scripts/multiwfn_catalog.py list --main
python3 scripts/multiwfn_catalog.py search "Hirshfeld-I"
python3 scripts/multiwfn_catalog.py show 20.11
python3 scripts/multiwfn_catalog.py plan igmh-interfragment
python3 scripts/multiwfn_catalog.py probe
```

The catalog contains 29 main functions and indexed subfunctions. `show 20.11`
can establish that IGMH is listed; only `plan igmh-interfragment` can return the
manual-grounded recipe. An unknown recipe exits `3` with
`MULTIWFN_RECIPE_NOT_ESTABLISHED`. Every plan keeps
`execution_authorized: false` and `native_execution_performed: false`.

## Use official invocation forms exactly

The pinned manual documents:

```text
Multiwfn
Multiwfn <input-file>
Multiwfn COCl2.fch -nt 36 -set /sob/tmp/settings.ini -silent
Multiwfn <input-file> -silent < commands.in > multiwfn.stdout 2> multiwfn.stderr
```

Treat the example filename, thread count, and settings path as placeholders.
The documented arguments are `-nt`, `-uf`, `-silent`, and `-set`. If
`settings.ini` cannot be found, do not assume those arguments took effect.
Record the exact settings file, thread/stack/shared-memory configuration, full
versus noGUI distribution, executable hash, banner, and both output streams.

The official site publishes Windows and Linux packages, including Linux noGUI.
The noGUI distribution cannot satisfy GUI/graph steps. The official site points
to a community macOS build that may differ in version; keep it blocked without
exact build and regression evidence. Review current license/citation terms on
the official download page; this Skill never accepts them for the user.

## Route by available information

- Basis-space orbital composition, Mayer order, PDOS/OPDOS, and related tasks
  require basis-function-bearing data such as eligible `.mwfn`, `.fch/.fchk`,
  Molden, or program-specific sources.
- `.wfn`/`.wfx` provide GTF wavefunction data but do not provide
  basis-function identity or virtual orbitals.
- Structure-only formats such as CIF, POSCAR, XYZ, or supported program inputs
  cannot support electronic-wavefunction analysis.
- Cube/CHGCAR/ELFCAR/LOCPOT routes require explicit grid, cell, unit, ordering,
  periodic, atom, and producer provenance.
- Direct converter or external-program routes are separate adapters and require
  separate authorization, versioning, and failure semantics.

Read [formats-and-handoffs.md](references/formats-and-handoffs.md) for the
full capability matrix. Prefer `.mwfn` or a verified basis-bearing export when
the task needs basis identity or virtual orbitals. Treat `.wfn/.wfx` as
real-space GTF sources, not general replacements for `.fch/.fchk`. For ECP
sources, record whether core density is absent, represented by EDF, or handled
another way; electron-count and topology claims depend on that convention.

For periodic work, choose explicitly between a finite cluster with
size/boundary convergence and a manual-supported periodic route. Do not infer
periodicity from a filename. Direct periodic wavefunction support is limited;
periodic ESP is not established by the pinned manual route.

## Apply the observable playbook

- For density, ELF/LOL, RDG/NCI/IGMH, grids, QTAIM critical points, paths, and
  basins, follow
  [real-space-and-topology.md](references/real-space-and-topology.md). Record
  mathematical conventions, box/spacing, search settings, topology closure,
  ECP/EDF handling, and numerical refinement. A BCP or colored surface is not
  by itself proof of a bond or interaction energy.
- For atomic charges, populations, orbital composition, Mayer/fuzzy/
  multicenter orders, localization, and aromaticity descriptors, follow
  [population-orbital-and-bond.md](references/population-orbital-and-bond.md).
  Require charge/population closure, exact atom/orbital maps, basis and
  partition sensitivity, and compatible references. These descriptors are not
  unique observables or formal oxidation states.
- For TDOS/PDOS/OPDOS, IR/Raman/UV/ECD/NMR spectra, transition assignments, and
  hole/electron grids, follow
  [dos-spectra-and-excitation.md](references/dos-spectra-and-excitation.md).
  Preserve raw levels/transitions, broadening and energy reference, paired-file
  identity, coefficient completeness, and whole-space closure. A molecular
  broadened level plot is not a periodic solid-state DOS.
- For batch preparation, prompt sentinels, fixed-output isolation, artifact
  checks, EOF handling, version-sensitive defects, and failure codes, follow
  [output-audit-and-troubleshooting.md](references/output-audit-and-troubleshooting.md).
  Report the highest evidence layer actually passed rather than the process
  exit status alone.

## Use only established recipes

The manual-backed recipe catalog currently covers:

- orbital composition: `8, 1, 1, 2, 3`;
- ELF cube: `5, 9, 2, 2`, producing fixed-name `ELF.cub`;
- Mulliken/Hirshfeld/ADCH/Hirshfeld-I prefixes: `7,5,1`, `7,1,1`,
  `7,11,1`, and `7,15,1`;
- Mayer and fuzzy bond-order prefixes: `9,1` and `9,7`;
- AIM topology GUI path: `2,2,3,0,<close-GUI>,8,0`;
- TDOS and the official system-specific PDOS/OPDOS tutorial;
- IGMH interfragment tutorial: `20,11,2,1-12,13-25,2,3`, producing
  `sl2r.cub` and `dg_inter.cub` among task-dependent grids;
- hole/electron workflow: `18,1,<matching-output>,2,1,3,10,11`, producing
  `hole.cub` and `electron.cub`.

Read [calling-and-recipes.md](references/calling-and-recipes.md) before using
any sequence. Only the orbital-composition and ELF examples are marked as
manual-documented stdin streams; all other routes remain interactive prefixes
or GUI workflows until an exact private transcript establishes every prompt,
export, filename, return token, and failure mode. Tutorial atom ranges, state
numbers, grid levels, energy windows, and thresholds are never transferable
defaults.

## Fail closed on execution and outputs

Use a fresh scratch directory because Multiwfn workflows can emit fixed
filenames. Reject existing outputs. Capture stdin/stdout/stderr and hash the
executable, settings, source, stream, and outputs. Stop on banner drift,
settings failure, input-family mismatch, prompt drift, GUI/noGUI mismatch,
missing/empty/unchanged artifacts, nonfinite data, or an unestablished recipe.

An EOF-related Fortran runtime message is not interpreted in isolation. Check
the exact prompt position, explicit main-menu `q`, earlier fatal text, and all
expected artifacts. Likewise, process exit zero or a plotted surface/table is
only technical completion, not scientific validation.

## Apply the narrow deterministic guard only where it fits

The existing guard validates an electronic-wavefunction source record, a
single exact noGUI inventory transcript profile, and a controlled charge-table
interchange format:

```text
python3 scripts/multiwfn_guard.py audit-source --source source.json --wavefunction source.wfx
python3 scripts/multiwfn_guard.py plan-menu --source source.json --wavefunction source.wfx --profile multiwfn-2026.7.15-linux-nogui --task wavefunction-inventory
python3 scripts/multiwfn_guard.py audit-transcript --transcript run.txt --profile multiwfn-2026.7.15-linux-nogui --task wavefunction-inventory
python3 scripts/multiwfn_guard.py parse-charge-table --source source.json --wavefunction source.wfx --table charges.txt
```

Do not treat that guard as a general menu executor or as validation of a
population method, topology, bond order, IGMH surface, spectrum, or chemical
claim. Apply observable-specific provenance, dimensional, conservation,
convergence, method-applicability, and interpretation checks after the parent
calculation has passed its own gates.

## Read the governing references

- [calling-and-recipes.md](references/calling-and-recipes.md): actual startup,
  recipes, prerequisites, outputs, checks, and failure semantics.
- [official-sources.yaml](references/official-sources.yaml): official URLs and
  supported claims.
- [environment-and-license.md](references/environment-and-license.md):
  distribution, settings, platform, and terms boundary.
- [formats-and-handoffs.md](references/formats-and-handoffs.md): input-format
  capabilities, converters, ECP/EDF and periodic rules, and paired-file
  handoffs.
- [real-space-and-topology.md](references/real-space-and-topology.md): fields,
  grids, weak-interaction methods, QTAIM searches, and basin closure.
- [population-orbital-and-bond.md](references/population-orbital-and-bond.md):
  charge models, compositions, bond orders, and interpretation limits.
- [dos-spectra-and-excitation.md](references/dos-spectra-and-excitation.md): DOS,
  spectra, parser boundaries, excitation coefficients, and grid closure.
- [output-audit-and-troubleshooting.md](references/output-audit-and-troubleshooting.md):
  run manifests, prompt and artifact auditing, failure taxonomy, and version
  drift.
- [version-matrix.yaml](references/version-matrix.yaml): exact program/manual
  profile and native-validation state.
- [weak-model-decision-table.json](references/weak-model-decision-table.json):
  machine routing; use the first ascending-priority match and the final
  fail-closed default.
- [fail-closed-contract.md](references/fail-closed-contract.md) and
  [task-evidence-profiles.json](references/task-evidence-profiles.json): narrow
  deterministic evidence gates.

Passing repository tests or a deterministic guard proves only the stated
technical contract. It never repairs parent-calculation quality or establishes
that a derived Multiwfn representation is physically unique or chemically
correct.
