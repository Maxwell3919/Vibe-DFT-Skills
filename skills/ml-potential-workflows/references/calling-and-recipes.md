# Provider calling and recipe boundary

Use [`provider-workflow-catalog.json`](provider-workflow-catalog.json) to discover an
exact provider/version operation and [`provider-recipes.json`](provider-recipes.json)
for its real CLI/API contract. Then return to the generic dataset, training, model,
evaluation and deployment audits in `SKILL.md`.

These layers are deliberately separate:

- **official documented**: exact tag/source or reviewed first-party docs expose the
  entry point;
- **generic guard**: metadata/lineage gates only, with no provider import or model
  deserialization;
- **native validated**: none on this host (`native-not-run`);
- **scientifically accepted**: requires independent data, convergence, evaluation,
  domain and deployment evidence beyond any CLI success.

Every recipe has `execution_authorized=false`.

## Provider selector

| Need | Exact registered route | Do not substitute |
|---|---|---|
| Train/evaluate a MACE model | MACE 0.3.16 `mace_run_train`, `mace_eval_configs`, `MACECalculator` | NequIP config/package semantics or an unverified LAMMPS exporter |
| Train/test/package/compile NequIP | NequIP 0.19.0 `nequip-train`, `nequip-package`, `nequip-compile` | Removed `nequip-evaluate`/legacy deploy commands |
| Use legacy OC20 EquiformerV2 | FairChem v1 1.10.0 `OCPCalculator` | FairChem v2 API/artifacts |
| Use UMA 1.2 | FairChem v2 2.21.0 `pretrained_mlip` + `FAIRChemCalculator` with explicit task | FairChem v1 models or an inferred task/reference convention |
| Use GemNet-OC v1 | Block pending exact model card/name/license and native regression | The Equiformer identifier or a guessed checkpoint |

## Version probes

None of these providers has a universal trustworthy `--version` convention in this
catalog. Resolve distribution identity with `importlib.metadata`, then capture help
from each actual console entry point. Executable path, Python environment, dependency
lock, accelerator/compiler stack and provider distribution must agree.

The exact tagged metadata currently establishes:

- MACE 0.3.16: Python >=3.9; console scripts include `mace_run_train`,
  `mace_eval_configs`, and `mace_create_lammps_model`.
- NequIP 0.19.0: Python >=3.10; console scripts include `nequip-train`,
  `nequip-package`, `nequip-compile`, and `nequip-prepare-lmp-mliap`.
- FairChem v1 1.10.0: Python >=3.9,<3.13 and a PyTorch 2.4-family dependency.
- FairChem v2 2.21.0: Python >=3.11,<3.14 and a PyTorch 2.8-family dependency.

The current Python 3.14 host is outside both FairChem ranges. No matching provider
distribution or CLI was found, so no import/help/model/download operation ran.

## MACE acceptance chain

Freeze config, exact data keys/units, group-disjoint splits, seeds, dtype/device,
cutoff/model/loss/stopping and output directories before `mace_run_train --config`.
Use validation for selection and keep test/OOD untouched. A restart requires the
exact checkpoint and unchanged scientific lineage; `--restart_latest` does not prove
it selected the intended checkpoint.

Treat `.model` as a serialized executable artifact: never load an untrusted file just
to inspect metadata. Evaluate immutable model/test pairs with `mace_eval_configs`,
then independently calculate predeclared MAE/RMSE/tail/slice/OOD metrics and device/
dtype regression. The catalog leaves `mace_create_lammps_model` blocked because its
exact argument and deployment contract was not validated here.

## NequIP acceptance chain

Use the 0.19.0 Hydra form `nequip-train -cp <config-dir> -cn <config-name.yaml>`.
Testing is a configured workflow stage; old `nequip-evaluate` and deployment commands
were removed. The official restart form uses `++ckpt_path=...` and warns that unsafe
config changes are not automatically detected, so diff the resolved config and allow
only the predeclared continuation change (commonly a larger `max_epochs`).

Build a `.nequip.zip` from an accepted checkpoint, record `nequip-package info`, and
compile on a deployment-like device/toolchain. AOTInductor ASE output
`.nequip.pt2` requires a C++17-capable environment and numerical regression against
the package. Checkpoints, packages, and compiled artifacts may contain or execute
code; never deserialize an untrusted artifact.

## FairChem acceptance chain

FairChem v2 is a breaking change from v1. For the validated legacy example, v1 uses
`OCPCalculator` and the exact model name
`EquiformerV2-31M-S2EF-OC20-All+MD`. For the v2 example, 2.21.0 uses
`pretrained_mlip.get_predict_unit('uma-s-1p2', ...)` and
`FAIRChemCalculator(..., task_name='omat')` for an audited inorganic-material case.

UMA weights are gated: account access, token use, network/download and cache writes
need separate authorization. Never record a token. Bind the exact downloaded bytes,
model card and model license because a model name alone is not identity. Choose the
task (`oc20`, `oc22`, `oc25`, `omat`, `omol`, `odac`, or `omc` where supported by the
selected model) from the input domain and enforce its charge/spin and DFT reference
conventions. In particular, OMat24 total-energy conventions must not be mixed with
Materials Project reference/correction conventions by assumption.

## Deployment gate shared by all providers

Before MD/relaxation, require accepted species and unit contracts, input domain,
force-energy consistency, stress/PBC convention, stable short pilots, conserved-
quantity checks where applicable, extrapolation/OOD monitor, stop action, rollback,
timestep/ensemble/temperature/pressure envelope and exact engine/adapter regression.
A package, compiled artifact, finite prediction, smooth trajectory, or low aggregate
error alone is insufficient.
