# Evaluation and deployment rules

## Frozen evaluation

An evaluation record binds exact dataset-audit, training-plan and model-audit report
hashes. It declares evaluator identity, held-out test policy, whether test data
influenced selection, target units, predeclared thresholds, measured metrics, slice
metrics and an OOD result.
The evaluator, slice-metric, frozen-threshold and three upstream report identities
must remain distinct evidence roles; a duplicated hash is not accepted as shorthand.

The frozen plan also predeclares the exact sorted IDs for every per-species,
configuration-class and OOD slice. Evaluation must return every and only those IDs;
choosing or renaming a slice after seeing test errors invalidates the gate.

For each required target, report at least MAE, RMSE and a high-quantile or maximum
absolute error in the same unit. Report force metrics whenever forces will drive
dynamics, and stress metrics whenever cells or pressure will evolve. Energy-only
accuracy cannot authorize force-driven MD.

The machine profile requires MAE, RMSE, and p95 absolute error for energy and forces,
plus the same three stress metrics when the dataset uses `all_frames` stress. A
deployment may request stress only when that stress policy and its independent
metrics survive through model and evaluation lineage.

Headline means do not replace:

- per-element and configuration-class slices;
- size/temperature/pressure/phase/defect or reaction-coordinate boundaries;
- OOD performance;
- conservation/stability trials;
- uncertainty or committee calibration when used as a monitor.

All thresholds are supplied before reading the test metrics. The auditor compares
exact named metrics; it never invents an acceptable error.

## Domain-shift ledger

Define the deployment domain as a machine-readable envelope, not “similar chemistry”.
At minimum classify:

- elements, combinations, stoichiometry, charge, spin, and model head/task;
- molecule/bulk/surface/interface/defect/adsorbate and coordination environment;
- cell/PBC, size, density, volume/strain, temperature, pressure, and phase;
- bond-breaking/formation, reaction coordinate, minimum distance, and force tails;
- reference DFT, energy zero, dispersion, pseudopotential, stress convention, and
  requested observable;
- engine, adapter, device, precision, compiler, timestep, ensemble, and run length.

Report test and OOD metrics by these axes. Interpolation in elemental composition can
still be extrapolation in coordination, phase, charge, spin, thermodynamic state, or
reference method. A foundation model's broad element list does not close this ledger.

## Ensembles and uncertainty

An uncertainty monitor is an operational heuristic until calibrated against reference
errors on a separate calibration set.

- A committee requires independently initialized/trained members with exact artifact
  identities. Clones of one checkpoint or only dropout resamples are not silently
  relabeled as an independent ensemble.
- Calibrate the chosen statistic against actual energy/force/stress errors by domain
  slice. Freeze threshold, statistic, aggregation (atom max, quantile, frame mean),
  unit, and fail action before deployment.
- Report discrimination and coverage, not only correlation. Low disagreement can be
  common-mode confident error because members share data, architecture, and reference
  bias.
- Combine calibrated model uncertainty with deterministic physics/domain sentinels:
  unsupported species/head/task, non-finite values, minimum distances, coordination,
  energy/force jumps, temperature/pressure bounds, and conservation drift.
- Active learning may consume the exploration/calibration pool, never the held-out
  test/OOD results. Relabeling and retraining create a new dataset/model version.

## Deployment envelope

A deployment record binds model and evaluation reports plus:

- target engine/version and adapter identity;
- exact species order and units;
- requested observables;
- structural, thermodynamic and compositional domain;
- timestep and ensemble limits;
- extrapolation monitor and numeric threshold;
- deterministic fail action (`stop_and_record` only in this candidate);
- rollback model hash;
- bounded pilot steps/atoms/temperature/pressure;
- external execution-authorization decision hash.

Model, evaluation, adapter, rollback and authorization identities must remain
distinct. In particular, an adapter hash cannot double as an authorization decision.

Deployment remains a limited pilot even after local gates pass. Production MD,
thermodynamic claims and scientific acceptance require engine-specific real-artifact
validation and expert review.

`npt` is forbidden unless stress is an explicitly requested observable backed by an
`all_frames` stress dataset and frozen independent stress metrics. Energy/force-only
evidence cannot control a pressure/cell degree of freedom.

## Adapter and MD compatibility matrix

| Provider artifact | Typical consumer | Compatibility evidence required |
|---|---|---|
| MACE `.model` | `MACECalculator` | Exact head, species, dtype/device, units, model bytes, ASE/provider versions |
| MACE derived LAMMPS artifact | Version-bound MACE/LAMMPS route | Exporter and LAMMPS build, type order, PBC/domain decomposition, direct-vs-engine regression; current exact recipe remains blocked |
| NequIP checkpoint/package | Provider test/package workflow | Config, package code/provenance, cutoff/types/units, trusted deserialization |
| NequIP compiled artifact | ASE, `pair_nequip`, Allegro, or ML-IAP target | Exact compile target/device/toolchain; target-specific output and multirank regression |
| FairChem v1 checkpoint | v1 `OCPCalculator` | v1 environment, exact model card/name/bytes, OC20 convention |
| UMA 1.2 gated checkpoint | v2 `FAIRChemCalculator` or reviewed v2 integration | Exact task, charge/spin inputs, gated artifact/license, provider/adapter version, domain and reference convention |

Before MD, compare identical structures through the accepted reference provider path
and the target engine/adapter. Check total energy, every force component, stress when
used, atom/type permutation, PBC/cell, neighbor cutoff, CPU/GPU and precision. Run
bounded minimization and short pilots before scaling. For NVE examine energy drift;
for thermostatted/barostatted runs also examine distributions and conserved/extended
quantities appropriate to the algorithm. Monitor geometry and uncertainty every
step/cadence and stop-and-record on any threshold crossing.

## Deployment failure response

| Finding | Required response |
|---|---|
| Finite but head/task/reference mismatched | Block; select the correct model identity and repeat all evaluation |
| Direct-vs-compiled/engine disagreement | Block deployment; isolate adapter, precision, neighbor, type, or unit difference |
| Good mean error but failed slice/tail/OOD | Preserve the failure; improve data/model under a new plan |
| Committee spread uncalibrated or low during obvious failure | Disable it as an authorization signal; add calibration and physical sentinels |
| Pilot leaves domain or violates physics sentinel | Stop and record the first failing frame; do not continue to collect a smooth-looking trajectory |
| NVE drift, unstable relaxation, or cell runaway | Reject the deployment envelope even when static MAE passes |
| Test/OOD informed retraining or threshold choice | Invalidate independence and create a new held-out set |

These operational checks do not authorize model loading or MD in this development
Skill and cannot raise `claim_ceiling=no_positive_claim`.
