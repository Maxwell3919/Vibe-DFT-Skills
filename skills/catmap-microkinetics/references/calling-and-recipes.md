# CatMAP calling surfaces and end-to-end recipes

## Evidence state

This development Skill targets the signed **CatMAP v0.4.1** tag (`ed04f91`). The
tagged `setup.py` and `catmap.__version__` still report `0.3.1`, while the online
manual identifies itself as `0.2.79` at revision `092f03a1`. Preserve all three
identities. A package version string or documentation header alone is not a
v0.4.1 environment receipt.

The calls below are either present in tagged source/first-party documentation or
are compositions of documented API calls. They were **not run locally** on
2026-07-19 because neither the `catmap` executable, a CatMAP distribution, nor a
discoverable `catmap` module was present. `documented` and `native-validated`
remain separate states; the recorded native state is `native-not-run`.

## Safe discovery layer

The catalog helper uses only Python metadata and static JSON. It does not import
CatMAP, execute a setup/log file, deserialize a pickle, or launch a command.

```bash
python3 -B skills/catmap-microkinetics/scripts/catmap_catalog.py groups
python3 -B skills/catmap-microkinetics/scripts/catmap_catalog.py search "rate control"
python3 -B skills/catmap-microkinetics/scripts/catmap_catalog.py show feature.cli.import
python3 -B skills/catmap-microkinetics/scripts/catmap_catalog.py recipes
python3 -B skills/catmap-microkinetics/scripts/catmap_catalog.py recipe recipe.run-mkm-model
python3 -B skills/catmap-microkinetics/scripts/catmap_catalog.py plan recipe.run-mkm-model
python3 -B skills/catmap-microkinetics/scripts/catmap_catalog.py probe
```

A plan is documentation, not authorization. `feature-only` recipes return exit
`3` and a blocking finding. The probe does not run `catmap --version` because the
tagged metadata/version disagreement makes that result insufficient anyway.

## Trust boundary

CatMAP model setup files are executable Python configuration. Tagged CLI source
shows that `catmap import model.mkm` constructs
`ReactionModel(setup_file='model.mkm')`; `catmap graphviz model.mkm` does the
same before graph generation. CatMAP log files are also Python, and saved data
uses pickle. Therefore:

- execute `.mkm`, `.log`, `.py`, `.pkl`, and `.pickle` only when their origin and
  exact bytes are trusted;
- use an isolated, tag-pinned environment with a dependency lock and no
  unnecessary network or credentials;
- never submit those native artifacts to `catmap_guard.py`;
- export trusted results to the declarative JSON interchange, bind content
  hashes, and audit that export separately.

## Canonical input set

The first-party tutorial uses three logical inputs:

1. a tab-separated energetics table;
2. a Python-like setup file such as `model.mkm`;
3. a submission script such as `mkm_job.py`.

The tutorial table names include `surface_name`, `site_name`, `species_name`,
`formation_energy`, `frequencies`, and `reference`. Extra columns are allowed by
the parser, but names and species/site correspondence must remain explicit.
Formation energies must share a declared reference. Frequencies are documented
as wavenumbers by default and converted through `frequency_unit_conversion`;
record the effective energy unit rather than relying on a default.

The setup must record at least:

- `rxn_expressions`, gas/surface/site species, site capacities, and descriptor
  names/ranges/resolution;
- parser, scaler, solver, mapper, and thermodynamics class/settings;
- `input_file`, temperature, gas pressures and standard-state convention;
- requested `output_variables`, rate normalization, precision/tolerances, and
  whether `use_numbers_solver` is enabled.

## Recipe A — trusted model run

First-party tutorial call shape:

```python
from catmap import ReactionModel

model = ReactionModel(setup_file='model.mkm')
model.run()
```

Run the reviewed submission script in the pinned environment:

```bash
python mkm_job.py
```

Expected native products include a model log, its configured pickle/data file,
solver progress, and requested map attributes. Exact names depend on the setup.
Treat any output as incomplete until all requested descriptor points, label
arrays, condition identity, solver branch, residuals, coverages/site closure,
rates, and hashes are captured. Process exit zero does not establish a solved
map or scientifically valid network.

## Recipe B — interactive inspection and graph rendering

Tagged CLI entry points:

```bash
catmap import model.mkm
catmap graphviz model.mkm
```

The import command opens an IPython session containing `model`; call
`model.run()` only after reviewing the executable setup and referenced input.
The graph command requires Graphviz and renders a reaction graph named from the
setup stem. A graph verifies neither rates nor pathway dominance.

Interactive changes must be serialized into a reviewed setup or execution
record. Shell history is not sufficient provenance.

## Recipe C — one point and descriptor maps

For a trusted initialized model, the documented single-point surface is:

```python
model.single_point_analysis([d1, d2])
```

The descriptor vector order is exactly `model.descriptor_names`; a bare list
carries neither names nor units. For rate and coverage maps:

```python
from catmap import analyze

vm = analyze.VectorMap(model)
vm.plot_variable = 'rate'
vm.log_scale = True
vm.plot(save='rate.pdf')

vm.plot_variable = 'coverage'
vm.log_scale = False
vm.plot(save='coverage.pdf')
```

Bind each output vector to `model.output_labels[variable]`. Preserve raw map rows
as `[descriptor_point, output_vector]`; do not infer a column order from a plot.
Record failed points and interpolation/clipping/log-scale policies. A smooth
figure can conceal solver failures or branch changes.

## Recipe D — production rates and degree of rate control

Request outputs before solving:

```python
model.output_variables += ['production_rate', 'rate_control']
model.run()

vm = analyze.VectorMap(model)
vm.plot_variable = 'production_rate'
vm.plot(save='production_rate.pdf')

mm = analyze.MatrixMap(model)
mm.plot_variable = 'rate_control'
mm.plot(save='rate_control.pdf')
```

Production, consumption, turnover frequency, and elementary-step rate are
different quantities. Preserve gas/parameter labels, active-site normalization,
and units. Degree of rate control is local to a model, branch, point, output,
perturbation convention, and numerical scale; it is not a unique rate-
determining-step declaration.

## Recipe E — free-energy diagram

```python
ma = analyze.MechanismAnalysis(model)
ma.plot(save='free_energy.pdf')
```

Record the mechanism/state sequence, surface or descriptor point, temperature,
pressure/potential, energy reference, and transition-state treatment. A chosen
sequence is an analysis input, not evidence that the mechanism is uniquely
identified.

## Recipe F — trusted output reload

The tutorial documents these trusted-only forms:

```python
model = ReactionModel(setup_file='model.log')
```

```bash
python -i model.log
```

Bind log and pickle bytes to the original setup, input table, provider identity,
dependencies, conditions, and solver configuration. Never load a log or pickle
received from an untrusted source. Reload success does not prove the data file is
the one that generated the log.

## Feature-only surfaces

Adsorbate interactions and electrochemistry are documented features, not
validated recipes in this development Skill.

- The interactions page explicitly warns of limited testing and compatibility
  constraints. First-order interactions require a separately validated parser,
  scaler, solver, response function, matrix provenance, and multiple-solution
  assessment.
- Electrochemical notation (`pe_g`/`ele_g`), RHE/SHE reference, CHE energies,
  `beta`, pH/standard state, potential-dependent barriers, and correction
  accounting need a dedicated profile.

The catalog therefore returns a blocking `CATMAP_FEATURE_ONLY_NO_VALIDATED_RECIPE`
for these recipes. Do not turn the documented setup tokens into an execution
plan without the missing evidence.

## VASP/QE and postprocessing handoff

CatMAP consumes energetics and thermochemistry; it does not validate the parent
electronic-structure calculation.

1. `vasp-rigorous-calculations` or `qe-rigorous-calculations` owns the structure,
   method, pseudopotential identity, numerical convergence, state/TS calculation,
   energy reference, and completion evidence.
2. A reviewed transformation normalizes those parent results into one
   thermochemistry dataset with species/reaction IDs, energy units/reference,
   corrections, conditions, uncertainties, and source hashes. Mixing unmatched
   parent protocols or references blocks the CatMAP run.
3. CatMAP execution records model/setup/input hashes, tag commit, dependency
   lock, solver branch/settings, conditions, requested outputs, and native
   artifact hashes.
4. A trusted exporter creates the declarative network, thermochemistry, and
   result JSON consumed by `catmap_guard.py`. Native files never cross this
   boundary as code.
5. Only a passing guard report may hand normalized maps/tables and label arrays
   to `dft-postprocess`. Postprocessing may plot or reformat evidence, but cannot
   repair balance, reference, solver, branch, uncertainty, or claim failures.

The current development lifecycle blocks shared routing and positive scientific
claims. This handoff is the required future contract, not an active route.

## Failure semantics

| Observation | Required state |
|---|---|
| Executable/package/module absent | `unavailable`; do not install implicitly |
| Metadata says 0.3.1 in a claimed v0.4.1 checkout | record the known conflict and require tag/tree identity |
| Online manual behavior is not confirmed by tagged source | `documented-not-version-matched`; block behavior-sensitive automation |
| Untrusted native setup/log/pickle | reject before load |
| Any missing/malformed descriptor point | structured guard failure; never crash or silently omit |
| Solver/map has missing points or branch disagreement | technical gate failed |
| Feature-only interaction/electrochemical recipe | exit `3`, blocked |
| Technical gates pass | at most `eligible_for_expert_review`; no mechanism or catalyst-ranking claim |

The machine-readable details are in `software-capability-catalog.json`,
`task-recipes.json`, `official-sources.yaml`, and `version-matrix.yaml`.
