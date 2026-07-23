# CatMAP modeling and validation guide

## Contents

1. [Evidence and version boundary](#evidence-and-version-boundary)
2. [Reaction network and species](#reaction-network-and-species)
3. [Energetics, frequencies, and thermochemistry](#energetics-frequencies-and-thermochemistry)
4. [Descriptors, scaling, solving, and mapping](#descriptors-scaling-solving-and-mapping)
5. [Outputs and their meanings](#outputs-and-their-meanings)
6. [Stiffness, convergence, and sensitivity](#stiffness-convergence-and-sensitivity)
7. [Validation workflow](#validation-workflow)
8. [Operational heuristics](#operational-heuristics)
9. [Primary sources](#primary-sources)

## Evidence and version boundary

Use this guide to review a trusted CatMAP model or to design a future provider adapter. It does
not authorize this development Skill to execute CatMAP or load native artifacts.

The provider target is the first-party `v0.4.1` tag at commit
`ed04f9146a787b0e63b6febd96d8fe3b314c251b`. The tag's package metadata still reports `0.3.1`,
and the online manual identifies itself as `0.2.79`. Treat tagged source as the authority for
behavior and use the online manual for concepts only when it agrees with that source. Preserve
all observed identities in an execution receipt instead of rewriting them into one version.

CatMAP setup (`.mkm`) and log files are executable Python, and native data files are pickle.
Review and hash their bytes before use, run only inside an isolated pinned environment, and never
load artifacts from an untrusted origin. Export trusted results to declarative data before using
the local guard.

The sections labeled **Official behavior** paraphrase first-party tagged source or documentation.
The final heuristics section is project-independent operating advice, not a CatMAP guarantee.

## Reaction network and species

### Official behavior

Declare the elementary network in ordered `rxn_expressions`. The tutorials use `_g` for gas
species, `_s` or another site suffix for explicit site types, `*` for a vacant surface site, and
hyphenated names for transition states. Documented expression shapes include:

```python
rxn_expressions = [
    '*_s + CO_g -> CO*',
    '2*_s + O2_g <-> O-O* + *_s -> 2O*',
    'CO* + O* <-> O-CO* + * -> CO2_g + 2*',
]
```

The middle state of an expression containing `<-> ... ->` is an explicit transition state. Do
not infer a computed transition state from an expression that omits one. Preserve expression
order because elementary-step output labels follow the model's reaction ordering.

Parsing the reaction expressions populates gas, adsorbate, transition-state, and site records.
Use `species_definitions` to supply conditions and site metadata, for example:

```python
species_definitions = {
    'CO_g': {'pressure': 1.0},
    'CO2_g': {'pressure': 0.0},
    's': {'site_names': ['111'], 'total': 1.0},
}
```

For multiple site types, give every site a distinct definition and total. Do not reuse a
single-site closure check for a multi-site lattice. If a species name cannot be interpreted as a
chemical formula, provide its elemental composition explicitly, e.g.
`species_definitions[name]['composition']`.

The default `TableParser` requires these exact tab-separated headers, independent of column
order:

- `surface_name`
- `site_name`
- `species_name`
- `formation_energy`
- `frequencies`
- `reference`

Additional columns are ignored unless a parser handler/configuration consumes them. A row with
fewer fields than headers may be skipped by the tagged parser after a warning, so record accepted
row counts and fail the surrounding workflow if a required row disappears.

The tutorial sometimes introduces a gas through a dummy self-reaction such as
`H2O_g -> H2O_g`. Treat that as legacy model-construction behavior, not chemical evidence.

### Required audit record

Record species IDs and types, elemental compositions, site occupancies, site capacities, reaction
expressions, parsed elementary steps, reversibility convention, and the mapping from every table
row to a model species/surface/site. Recompute elemental and site balance independently. A parsed
or balanced network can still omit real chemistry.

## Energetics, frequencies, and thermochemistry

### Official behavior

The tutorial input table treats `formation_energy` as the common-reference energetic contribution
to which thermal corrections are later added. All gases, adsorbates, and transition states must
share the same declared reference scheme. Keep the parent electronic-structure calculation,
reference conversion, and CatMAP correction as separate provenance layers.

The default `frequency_unit_conversion` in the tagged `TableParser` is `1.239842e-4`, converting
wavenumbers in `cm^-1` to eV. The parser can borrow or estimate missing frequencies according to
`estimate_frequencies` and `frequency_surface_names`, and can ultimately produce an empty list.
Such fallback behavior is model input provenance; it is not evidence that vibrational
thermochemistry is adequate.

The tagged tutorials expose these gas correction modes:

- `shomate_gas`
- `ideal_gas`
- `zero_point_gas`
- `fixed_entropy_gas`
- `frozen_gas`

They expose these adsorbate correction modes:

- `frozen_adsorbate`
- `harmonic_adsorbate`
- `hindered_adsorbate`
- `zero_point_adsorbate`

Record the exact mode, parameters, source data, temperature, gas pressure or concentration
convention, and standard state. If the table already contains free energies or thermal
corrections, do not add the same zero-point, enthalpy, or entropy contribution again. A frozen
mode may prevent double counting but does not validate the supplied free energy.

For every activated step, retain initial-, transition-, and final-state free energies at the same
condition and reference. Check that the forward and reverse barriers are non-negative within a
predeclared tolerance and that their difference closes to the reaction free energy. Scaling a
transition-state energy does not replace transition-state provenance.

### Required audit record

Record, per species and step:

- source calculation or dataset hash and electronic-structure method;
- raw energy, reference conversion, vibrational data, and each thermal correction;
- units before and after conversion;
- condition and standard-state identity;
- frequency fallback/estimation mode and source species/surface;
- forward and reverse barriers and cycle-closure residual;
- uncertainty or evidence class.

Do not infer a rate unit from an energy unit. CatMAP's numerical values inherit the configured
site, pressure, prefactor, and standard-state conventions; the portable record must state them.

## Descriptors, scaling, solving, and mapping

### Official behavior

The tagged `ReactionModel.load()` defaults are:

| Component | Tagged default |
|---|---|
| mapper | `MinResidMapper` |
| parser | `TableParser` |
| scaler | `GeneralizedLinearScaler` |
| solver | `SteadyStateSolver` |
| thermodynamics | `ThermoCorrections` |
| numerical representation | `mpmath` |
| decimal precision | `75` |
| number-of-sites solver | `use_numbers_solver=True` |
| data file | `data.pkl` |

The v0.4.1 README states that the number-of-sites formulation is now the default and that
`use_numbers_solver=False` requests legacy behavior corresponding to versions through 0.3.2.
Never toggle this setting merely to obtain convergence; it changes solver behavior and requires a
separate comparison profile.

The standard architecture maps:

`named descriptor point -> scaler -> reaction parameters -> solver -> outputs`

The mapper traverses descriptor space and can reuse a nearby converged coverage/number solution
as an initial guess. Therefore map traversal and any seed map are part of solver provenance, not
just a plotting detail.

Declare `descriptor_names`, `descriptor_ranges`, and `resolution` together. A descriptor vector
is positional and is uninterpretable without `descriptor_names`. The generalized linear scaler
accepts coefficient constraints including numeric values, `+`, `-`, ranges such as `0:3`, and
`None`; transition-state constraints include `initial_state`, `final_state`, and `BEP`. Preserve
the complete fitted coefficient matrix, constraints, training surfaces, residuals, and
extrapolation flags.

### Required audit record

For each run, bind the exact setup and input hashes to component classes, all non-default
settings, descriptor names/order/units/domain/grid, scaling training rows, constraint dictionary,
coefficient matrix, solver formulation, precision, tolerance, iteration/bisection limits, mapper
path, seed points, and prior maps. A descriptor-space fit can interpolate smoothly while violating
the underlying chemistry or extrapolating beyond its training surfaces.

## Outputs and their meanings

### Official behavior

Request only the outputs needed for the task. In the tagged solver:

- `coverage` reports the steady-state surface-species coverage vector;
- `rate` reports signed net elementary-step rates;
- `turnover_frequency` sums signed elementary-step rates for each gas according to stoichiometry;
- `production_rate` is `max(turnover_frequency, 0)` for each gas;
- `consumption_rate` is `max(-turnover_frequency, 0)` for each gas;
- `selectivity` normalizes positive product rates or negative reactant rates over the selected
  gas sets and optional weights;
- `rate_control` is indexed by `[gas_names, parameter_names]`;
- `selectivity_control` is indexed by `[gas_names, parameter_names]`;
- `rxn_order` is indexed by `[gas_names, gas_names]`.

If `products` and `reactants` are unset, the tagged solver derives them from the signs at the
first evaluated state. Declare fixed sets for a comparison across descriptor points, and record
any weights used for elemental selectivity. Never compare `rate`, gas TOF, production rate, and
selectivity as though they were the same observable.

The degree of rate control implemented by the mean-field solver corresponds to the local
derivative of log gas rate with respect to `-G_j/kT`. A positive value means that locally
stabilizing that parameter increases the selected rate under the model's sign convention. The
reaction-order calculation is likewise a local finite difference with respect to gas pressure.

Every map row has the form `[descriptor_point, output_vector]`. Decode vectors through
`model.output_labels[variable]`; never infer ordering from a plot or from species alphabetical
order. Retain failed/missing points. The tagged all-output tutorial itself warns that some output
combinations can crash, so do not use `output_variables=['all']` as a provider validation test.

### Required audit record

Store raw labeled arrays before plotting, along with rate units and active-site normalization,
condition, descriptor point, solver branch, residual, site closure, and output-generation status.
For selectivity and sensitivity, store product/reactant sets, weights, perturbation convention,
parameter labels, and undefined/zero-rate handling.

## Stiffness, convergence, and sensitivity

CatMAP uses high-precision numerical root finding because mean-field kinetic systems can be
stiff. A returned object, a process exit code of zero, or a visually smooth map is not a
steady-state certificate.

Require all of the following for every accepted descriptor point:

1. finite coverages/numbers and rates;
2. non-negative coverages within tolerance and per-site closure;
3. an independently recomputed finite steady-state residual below a predeclared tolerance;
4. iteration and termination status with no hidden missing point;
5. agreement of the final state from multiple physically distinct initial guesses;
6. stable observable values under increased precision and tighter numerical settings;
7. consistent results when the descriptor grid is traversed from different directions;
8. species-production closure from stoichiometry and elementary rates.

If converged initial guesses reach different fingerprints or rates, report multiple branches.
Do not silently select the smallest residual as the physical solution. Steady state alone does not
establish kinetic stability; transient/eigenvalue evidence would need a separate profile.

Rate control, selectivity control, and reaction order are numerical derivatives. Repeat them at
at least two declared perturbation scales. Reject coefficients that change sign or material
magnitude without a justified convergence region, or whose perturbed solves change branch or
fail. Near-zero rates make logarithmic sensitivities ill-conditioned; report them as undefined or
below a declared floor rather than as a mechanistic zero. A zero matrix returned after an internal
Jacobian failure is failure evidence, not proof that no parameter controls the rate.

## Validation workflow

1. Hash and review the trusted setup, table, submission script, tag checkout, and dependency lock.
2. Parse the network; independently check elemental/site balance and species-table coverage.
3. Reconstruct every free energy and barrier from recorded components at the target condition.
4. Inspect scaler training coverage, constraints, fit residuals, and descriptor extrapolation.
5. Solve predeclared single points from multiple initial states before mapping a grid.
6. Map with at least two traversal/seed strategies and retain all failed points and branches.
7. Recompute site closure, production closure, and labeled observables independently.
8. Repeat precision/tolerance/grid and sensitivity perturbation checks.
9. Export a hash-bound declarative package; run the local guard without loading native files.
10. Keep the maximum conclusion at `eligible_for_expert_review` until a human reviews model-form,
    parent DFT, experimental domain, and uncertainty evidence.

## Operational heuristics

These practices come from general microkinetic-model use and are not official CatMAP guarantees:

- Start from one hand-checkable descriptor point before a large map; diagnose balance, reference,
  and labels there.
- Use the first minimum of a physically justified free-energy/rate trend only as a diagnostic, not
  as an automatic descriptor bound or catalyst optimum.
- Seed stiff maps from neighboring points but rerun selected rows in reverse order and from
  independent states to expose path dependence.
- Increase decimal precision together with a documented residual target; precision alone cannot
  repair a poor network, discontinuous scaler, or missing transition state.
- Plot coverage, residual, branch identity, and missing-point masks alongside activity. A volcano
  plot without those layers is incomplete diagnostic evidence.
- Perturb one clearly identified energetic parameter at a time and preserve thermodynamic cycle
  consistency. An arbitrary barrier-only perturbation can create an unphysical sensitivity.
- Compare model predictions only inside a domain supported by parent energetics and scaling data.
  Treat ranking changes under plausible model choices as model-form uncertainty.

## Primary sources

Checked against first-party material on 2026-07-22:

- tagged source and tutorials: https://github.com/SUNCAT-Center/catmap/tree/v0.4.1
- code overview: https://catmap.readthedocs.io/en/latest/topics/code_overview.html
- input-file tutorial: https://catmap.readthedocs.io/en/latest/tutorials/generating_an_input_file.html
- model tutorial: https://catmap.readthedocs.io/en/latest/tutorials/creating_a_microkinetic_model.html
- refinement tutorial: https://catmap.readthedocs.io/en/latest/tutorials/refining_a_microkinetic_model.html
- output variables: https://catmap.readthedocs.io/en/latest/topics/output_variables.html
- output access and labels: https://catmap.readthedocs.io/en/latest/topics/accessing_reformatting_output.html
- parser/scaler/solver/thermodynamics API references:
  https://catmap.readthedocs.io/en/latest/reference/catmap.parsers.html,
  https://catmap.readthedocs.io/en/latest/reference/catmap.scalers.html,
  https://catmap.readthedocs.io/en/latest/reference/catmap.solvers.html, and
  https://catmap.readthedocs.io/en/latest/reference/catmap.thermodynamics.html
