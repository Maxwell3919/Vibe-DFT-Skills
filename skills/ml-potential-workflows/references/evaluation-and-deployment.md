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
