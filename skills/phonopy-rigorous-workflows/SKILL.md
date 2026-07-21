---
name: phonopy-rigorous-workflows
description: Discover, plan, call, audit, and scientifically review version-pinned Phonopy workflows using the official 4.3.1 command/source catalog, the v4 phonopy-init versus phonopy split, calculator-specific finite-displacement and direct-force-constant routes, bands, mesh, DOS/PDOS, thermal properties, NAC, QHA, Gruneisen, random-displacement and experimental MLP/SSCHA boundaries, explicit documentation-drift stops, and exact lineage. Use when preparing or collecting VASP/QE/other force calculations, choosing a Phonopy command or helper, checking inputs/outputs, diagnosing version migration, or deciding whether a phonon result supports a scientific claim.
---

# Phonopy Rigorous Workflows

Use the official-manual route first. This skill is pinned to Phonopy `4.3.1`,
official tag commit `baf530aed09071e1221b3c191918a168fc5f1d9b`, released
2026-07-01 and checked 2026-07-19. The maintainer machine had no Phonopy
distribution or console script, so the bundled calls are `native-not-run`.

The unversioned official site was rechecked on 2026-07-22 and already rendered
some input, settings, and QHA pages as `4.4.0`. Keep this profile on exact
`4.3.1`; block 4.4.0 until its source, parser, migration, fixtures, and native
help are reviewed.

Never collapse these evidence layers:

1. the tag-pinned source lists an entrypoint or option;
2. official documentation establishes a recipe;
3. an exact installed executable was run and its outputs were validated.

This repository establishes layers 1 and 2 for the recorded recipes, not 3.

## Search before generating a command

```text
python3 scripts/phonopy_catalog.py kinds
python3 scripts/phonopy_catalog.py list --kind entrypoint
python3 scripts/phonopy_catalog.py search "projected DOS"
python3 scripts/phonopy_catalog.py show phonopy-qha
python3 scripts/phonopy_catalog.py plan vasp-finite-displacement
python3 scripts/phonopy_catalog.py probe
```

[official-command-catalog.json](references/official-command-catalog.json)
indexes all 15 v4.3.1 console scripts, current parser option families, 17
calculator selectors, capabilities, and official-documentation conflicts.
[task-recipes.json](references/task-recipes.json) records whether an exact
recipe is established. An official feature listing is not a recipe, and a
recipe is not native execution.

If no recipe exists, return `PHONOPY_RECIPE_NOT_ESTABLISHED`; do not construct
an argv by analogy. Read
[calling-and-recipes.md](references/calling-and-recipes.md) for exact calls,
inputs, outputs, failure modes, and scientific checks. Then apply
[production-acceptance-checklists.md](references/production-acceptance-checklists.md)
for the force-calculator handoff, supercell and displacement convergence,
FORCE_SETS type, residual-force, force-constant, NAC, property, and QHA gates.
Every experience-derived starting point in that reference is labeled
`operational heuristic` and still requires project-specific validation.

## Respect the v4 boundary

Use `phonopy-init` for displacement setup, initial random snapshots, force
collection, residual-force subtraction, direct VASP force-constant import, and
symmetry inspection. Use `phonopy` for calculations from a phonopy YAML-like
file: band, mesh, q points, DOS/PDOS, thermal properties, irreps, modulation,
NAC-aware properties, fitting, and related products. `phonopy-load` is a
deprecated alias of `phonopy`.

Do not emit old v3 forms such as `phonopy -d`, `phonopy -f`, or
`phonopy --symmetry -c`. The v4 primitive-matrix default is `auto`, not the v3
identity; record the resolved matrix. The main v4 CLI removed `--nac`: NAC is
automatic when compatible BORN/YAML parameters exist and `--nonac` disables it.
The pinned parser also has no `--symfc`, `--br`, or VASP-Born `--st` option.

For an installed copy, do not guess `--version`; the pinned parsers do not
register it. Check identity with:

```text
command -v phonopy
command -v phonopy-init
python -c 'import phonopy; print(phonopy.__version__)'
phonopy -h
phonopy-init -h
```

Record package and executable hashes, platform, Python/dependency versions,
backend banner, environment lock, and optional extras. `seekpath` is needed for
`--band auto`; CP2K parsing and pypolymlp routes have separate optional
dependencies. Never auto-install a missing package.

## Route the workflow

For VASP finite displacement:

```text
phonopy-init -d --dim 2 2 2 --pa auto -c POSCAR-unitcell
# one accepted fixed-ion VASP force run per displaced structure
phonopy-init --vasp --sp -f disp-{001..N}/vasprun.xml
phonopy --band auto --band-points 101 phonopy_params.yaml
```

For Quantum ESPRESSO finite displacement:

```text
phonopy-init --qe -d --dim 2 2 2 --pa auto -c NaCl.in
# one accepted fixed-ion pw.x force run per displaced structure
phonopy-init --qe --sp -f NaCl-001.out NaCl-002.out ...
phonopy --band auto --band-points 101 phonopy_params.yaml
```

Call `vasp-rigorous-calculations` or `qe-rigorous-calculations` for every
external parent. Phonopy-readable forces do not establish DFT completion, SCF
convergence, force validity, pseudopotential consistency, or numerical
convergence. Require exactly one completed result per displacement, correct
order, fixed atom mapping, units, finite values, and matching inputs.

For VASP DFPT force constants:

```text
phonopy-init --fc vasprun.xml
```

This import is VASP-only. Prove the Hessian exists and matches the intended
supercell and atom order. For a random type-2 displacement-force dataset, use a
fitter explicitly:

```text
phonopy phonopy_params.yaml --fc-calculator symfc --writefc
```

For common properties:

```text
phonopy --mesh 31 31 31 --dos phonopy_params.yaml
phonopy --mesh 41 41 41 --pdos "1, 2" phonopy_params.yaml
phonopy --mesh 31 31 31 -t phonopy_params.yaml
phonopy --band "0 0 0  0.5 0 0  0.5 0.5 0" --band-points 101 phonopy_params.yaml
phonopy --irreps 0 0 0 phonopy_params.yaml
```

Converge the actual q mesh, broadening, temperature range, band path density,
supercell, and displacement amplitude for each observable. PDOS indices follow
the primitive-cell atom order. Preserve signed frequencies and inspect
eigenvectors of suspicious modes; never turn a negative frequency into an
automatic stability verdict.

For VASP NAC:

```text
phonopy-vasp-born vasprun.xml > BORN
phonopy --band "<checked-path>" phonopy_params.yaml
```

For QE NAC:

```text
phonopy-qe-born NaCl.in NaCl.ph.out > BORN
phonopy --band "<checked-path>" phonopy_params.yaml
```

Validate response-calculation completion, dielectric and Born-charge tensors,
primitive mapping, units, charge neutrality, and activation in the Phonopy log.
Do not add the removed main `--nac` option.

For QHA, provide at least five volume points and ordered thermal-property files:

```text
phonopy-qha e-v.dat <thermal-properties-in-volume-order...>
```

Require identical normalization and temperature grids, a volume range that
brackets equilibrium, converged static energies and phonons, stable EOS fits,
and explicit imaginary-mode policy. Supply one extra high-temperature point for
numerical differentiation. The official page warns that bulk modulus under
nonzero `--pressure` is incorrect; QHA also does not perform full anisotropic
free-energy minimization.

For mode Gruneisen parameters:

```text
phonopy-gruneisen orig plus minus --dim="2 2 2" --pa=auto \
  --mesh="20 20 20" -c POSCAR-unitcell
```

Require consistent constrained-volume relaxation, mapping, calculator settings,
volume bracketing, finite-difference step, and three independently accepted
phonon models. Inspect divergence near Gamma and low/imaginary modes.

Random-displacement, pypolymlp, and SSCHA routes require explicit seed, sample
count, amplitude/temperature, dataset type, fitter version, validation split,
error metrics, configuration coverage, and target-observable convergence.
pypolymlp/SSCHA remains experimental because current official prose conflicts
with the pinned parser and dependency manifest.

## Treat documentation drift as evidence

Current official pages mix v4 source truth with older commands and banners.
The catalog records the conflicts, including old `phonopy -f`, removed
`--nac`, missing `--symfc/--br/--st`, `phonopy-proplot` spelling, old example
banners, PDOS filename drift, and interface-navigation lag. Resolve conflicts in
this order: tag-pinned source/parser; same-version migration/changelog;
same-version command reference; official tutorial; unversioned prose.

Do not infer success from exit code alone. Some helpers have unusual versioned
exit behavior. Require a new or intentionally replaced output, nonempty and
parseable content, expected shape/schema, source hashes, complete stdout/stderr,
units, mapping, and an observable-specific scientific check.

## Use the deterministic guard for lineage, not usage discovery

The existing guard audits narrow, deterministic evidence and never launches
Phonopy:

```text
python3 scripts/phonopy_guard.py audit-lineage --manifest workflow.json
python3 scripts/phonopy_guard.py plan-stage --manifest workflow.json --stage displacements
python3 scripts/phonopy_guard.py parse-frequency-table --manifest workflow.json --table band.txt
```

It does not replace the official command catalog, recipes, exact executable
help, external-calculator validation, or real scientific convergence.

For low-reasoning routing, use
[weak-model-decision-table.json](references/weak-model-decision-table.json) as
the machine source of truth and
[low-reasoning-decision-table.md](references/low-reasoning-decision-table.md)
as human guidance. Apply the first ascending-priority match and fail closed when
no route is established.

## Claim boundary

A valid lineage and parseable Phonopy output do not prove force-calculator
convergence, adequate supercell/displacement/q-mesh sampling, acoustic-sum-rule
quality, suitable LO-TO treatment, absence of numerical artifacts, dynamical or
thermodynamic stability, experimental agreement, or a causal materials claim.
Report those only with observable-specific convergence and expert review.

Use [official-sources.yaml](references/official-sources.yaml) for provenance,
[version-matrix.yaml](references/version-matrix.yaml) for version policy,
[environment-and-license.md](references/environment-and-license.md) for runtime
and redistribution boundaries, and
[task-evidence-profiles.json](references/task-evidence-profiles.json) for
deterministic lineage requirements.
