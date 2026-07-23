# GPUMD v5.3 NEP model workflow

Use this reference for NEP data, training, restart, validation, and deployment
planning. The current guard does not parse `nep.in`, training data, `nep.txt`,
or NEP outputs, so this route remains design-only.

## Contents

- [Separate construction from deployment](#separate-construction-from-deployment)
- [Close the dataset contract](#close-the-dataset-contract)
- [Define and train the model](#define-and-train-the-model)
- [Restart training safely](#restart-training-safely)
- [Validate beyond loss curves](#validate-beyond-loss-curves)
- [Deploy in GPUMD](#deploy-in-gpumd)
- [Route failures](#route-failures)

## Separate construction from deployment

The v5.3 repository builds two ordinary executables:

- `nep` constructs or evaluates a NEP model using fixed-name `nep.in`,
  `train.xyz`, and `test.xyz` inputs;
- `gpumd` uses a resulting `nep.txt` potential for simulation.

Treat these as different evidence chains. A completed training process does not
prove test accuracy, application-domain validity, stable MD, or support for a
particular observable. Bind the training code/build, configuration, input data,
randomness, restart ancestry, and resulting model hash before deployment.

GPUMD v5.3 contains an internal documentary inconsistency: `nep.in` says NEP3
and NEP4 are supported, while the v5.3 release deprecates NEP3 and the bundled
NEP formalism page says only NEP4 is supported. Use NEP4 for a new v5.3 plan.
Treat any NEP3 continuation as unresolved until exact source behavior, model
format, and a lawful fixture are independently verified. Do not infer the
accepted version set from newer rolling documentation.

## Close the dataset contract

Official v5.3 `train.xyz`/`test.xyz` facts:

- each structure is extended XYZ with mandatory `Lattice`, total `energy`, and
  `Properties` containing species, positions, and force(s);
- length/position use Å, total energy eV, force eV/Å, total virial eV, and
  stress eV/Å³;
- if both virial and stress occur, virial is used;
- periodic boundaries are assumed in all directions and small cells are
  replicated internally when needed;
- energy and virial are per-cell targets, not per-atom input values;
- optional configuration weight and optional BEC data are supported;
- the manual warns that single-precision training loses accuracy when a
  reference energy is below −100 eV/atom.

For every structure record the source calculation identity, electronic-
structure method, convergence state, atom/species order, cell/boundary meaning,
energy reference, force/virial convention, unit conversion, and license. Reject
mixed conventions or unverifiable labels.

Operational heuristic: split train/validation/test data by physically related
groups—trajectory, parent structure, composition, phase, strain/temperature
regime, or active-learning cycle—rather than randomly splitting neighboring
frames. Near-duplicate frames across splits can produce optimistic errors.

Build dataset coverage around the intended deployment domain, including likely
high-energy, strained, defect, interface, transition, and short-distance
configurations where applicable. Do not add arbitrary extremes that violate
the reference method without documenting their role.

## Define and train the model

`nep.in` uses one keyword plus parameters per noncomment line. In v5.3, `type`
is mandatory and must precede `type_weight`; other documented keywords have
defaults. Important groups include:

- model/version/type and optional charge/dipole/polarizability mode;
- radial/angular cutoffs, basis sizes, angular orders, and hidden neurons;
- energy/force/virial loss weights and regularization;
- batch, population, generation count, and optional ZBL behavior.

Never equate documented defaults with a validated architecture. Record the
complete `nep.in`, even for defaulted values needed to reproduce or interpret
the model. Pin the exact v5.3 semantics for every keyword used.

`loss.out` reports every 100th generation. For a potential model, it includes
total/regularization terms and train/test energy, force, and virial RMSE. The
documented RMSE units are eV/atom for energy and virial, and eV/Å for force.
Inspect all target components; a decreasing total loss can hide degradation in
the component that controls the intended application.

Operational heuristic: retain immutable checkpoints and a training manifest,
monitor train/test separation, and define early-stop/model-selection logic
before examining the desired application result. Multiple training seeds can
expose optimizer/model variance, but they do not replace data-domain tests.

## Restart training safely

`nep.restart` is continuously updated during optimization. If it is present,
`nep` starts from that saved state. The v5.3 manual requires descriptor-related
hyperparameters in `nep.in` to match those used to create the restart.

Before a restart:

1. preserve and hash `nep.restart`, `nep.in`, train/test data, executable, and
   the parent `loss.out`;
2. verify descriptor hyperparameters and data identity rather than relying on
   filenames;
3. record parent generation/checkpoint and child segment identity;
4. keep loss/output segments distinguishable and detect stale appended data;
5. treat any changed dataset, labels, species order, model form, or incompatible
   hyperparameter as a new training lineage unless authoritative semantics
   prove continuation is valid.

The opaque restart is recoverability evidence, not proof that two runs are
bitwise identical across builds or hardware.

## Validate beyond loss curves

Require application-relevant validation at several layers:

1. **data integrity** — units, labels, energy reference, composition, duplicate
   policy, and split independence;
2. **held-out prediction** — energy/force/virial errors by composition,
   structure family, energy range, and force magnitude, not only one aggregate;
3. **physical sanity** — finite predictions, symmetries/invariances, sensible
   short-range behavior, and no obvious discontinuity near cutoffs;
4. **observable validation** — structures, elastic/phonon/defect/reaction or
   thermodynamic/transport quantities required by the actual claim;
5. **dynamical stress tests** — stable, energy-conserving NVE across relevant
   temperatures/pressures and detection of excursions outside training domain;
6. **reference spot checks** — new configurations selected from intended MD or
   search, evaluated independently with the reference method;
7. **uncertainty/domain policy** — explicit stop/relabel/retrain response when
   an ensemble or committee indicates extrapolation.

Operational heuristic: use a committee or repeated fits only as a domain-risk
signal. Low disagreement among similarly biased models is not accuracy. Close
the loop with independent reference calculations and preserve every added
configuration's acquisition provenance.

Do not use test RMSE as the sole acceptance condition. Small average errors can
coexist with catastrophic local errors, unstable MD, wrong phase ordering, or
poor heat-current/virial behavior.

## Deploy in GPUMD

The v5.3 `nep.txt` output contains the trained model parameters and can be used
by `gpumd` through the `potential` command. Before deployment, bind:

- exact `nep.txt` SHA-256 and independent redistribution/use rights;
- v5.3/NEP format compatibility and type/species order;
- training code/build and `nep.in` identity;
- complete train/test/reference provenance and validation report;
- approved chemical, structural, thermodynamic, and observable domain;
- short-range/ZBL and long-range/dispersion treatment where applicable;
- uncertainty/extrapolation response and model version replacement policy.

Perform a bounded static and MD smoke comparison before production. A model
that loads successfully has passed only a format/interface gate.

## Route failures

| Symptom | First checks | Required response |
|---|---|---|
| parser/type error | exact v5.3 keywords, mandatory `type`, species order, extxyz columns | correct documented input; do not borrow rolling syntax |
| non-finite/diverging loss | labels/units, extreme configurations, weights, restart compatibility | quarantine evidence and diagnose before retuning |
| low train error/high test error | split independence, coverage, capacity/regularization | revise data/model with a declared new lineage |
| both errors low but MD fails | local outliers, short contacts, time step, reference-domain coverage | add reference spot checks; do not accept aggregate RMSE |
| virial/transport failure | virial labels, stress conversion, heat-current-relevant validation | withhold pressure/transport claims |
| restart changes trajectory unexpectedly | restart/data/config/build hashes and output segmentation | treat as a new or discontinuous training segment |
| fast model but wrong observable | model-domain and observable benchmarks | scientific acceptance fails regardless of throughput |

Primary v5.3 sources: [`nep.in`](https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/doc/nep/input_files/nep_in.rst),
[`train.xyz`/`test.xyz`](https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/doc/nep/input_files/train_test_xyz.rst),
[`loss.out`](https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/doc/nep/output_files/loss_out.rst),
[`nep.restart`](https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/doc/nep/output_files/nep_restart.rst),
and [`nep.txt`](https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/doc/nep/output_files/nep_txt.rst).
