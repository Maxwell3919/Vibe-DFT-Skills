# Training and transfer playbook

Use this reference after the dataset audit and provider matrix. Every provider
statement is labeled **Official fact**; every recommendation labeled **Operational
heuristic** is conservative practitioner guidance rather than a provider default,
validated threshold, or native evidence. Version boundaries and source locators are
in [`official-sources.md`](official-sources.md).

## Contents

1. Select the provider and workflow mode
2. Freeze reference energy, force, and stress conventions
3. Plan loss, learning rate, checkpoints, and restarts
4. MACE 0.3.16 and foundation-model heads
5. NequIP 0.19.0 packages and fine-tuning
6. FairChem v1/v2 and UMA task routing
7. Cross-provider fine-tuning gate
8. Frequent failure modes

## 1. Select the provider and workflow mode

| Need | Candidate route | Required boundary |
|---|---|---|
| Train a local equivariant potential from accepted labels | MACE 0.3.16 or NequIP 0.19.0 | Select by validated data/config/deployment support; no framework is universally superior |
| Fine-tune a documented MACE foundation model | `mace-python`, `fine_tune` | Bind base artifact, model card, head, elements, DFT reference, E0s, and fine-tune protocol |
| Fine-tune a packaged NequIP-family model | `nequip-python`, `fine_tune` | Bind package, model loader, cutoff, types, shifts/scales, outputs, and package path |
| Evaluate legacy OC20 GemNet-OC/EquiformerV2 | FairChem v1 profile | Keep v1 environment/API/artifact; GemNet-OC remains blocked without exact model evidence |
| Evaluate UMA 1.2 | `fairchem-v2-uma`, `evaluate_pretrained` | Bind exact gated bytes and one explicit UMA task/reference convention |
| Fine-tune UMA | Documented future provider handoff only | Current generic matrix does not permit FairChem fine-tune mode; do not bypass it |

**Operational heuristics**

- Start from the downstream observable and execution engine. Species coverage, force
  smoothness, stress support, long-range physics, cutoff/receptive field, memory,
  compilation, MPI/device support, and license/access can eliminate a provider before
  benchmark accuracy matters.
- Compare providers on one immutable split and reference protocol. Equal names such as
  “energy MAE” are not comparable until total/per-atom normalization, units, offsets,
  species, and slices match.
- Prefer the smallest model that clears predeclared accuracy, stability, and throughput
  gates on the target hardware. A larger or newer foundation model is not automatically
  safer under domain shift.

## 2. Freeze reference energy, force, and stress conventions

### Energy

**Official facts**

- MACE supports explicit atomic reference energies (`E0s`) or an `average` least-squares
  estimate. Foundation/fine-tuning documentation treats E0 compatibility as a distinct
  requirement.
- NequIP energy models use per-type shifts/scales; the manual recommends same-method
  isolated-atom shifts when the dissociation limit matters and permits modifying them
  during fine-tuning for a changed reference method.
- UMA tasks represent different datasets and DFT levels. `omat`, `omol`, `oc20`,
  `oc22`, `oc25`, `odac`, and `omc` are not interchangeable labels. The current UMA
  manual notes that its OC20 task was recomputed to total energies, unlike legacy OC20
  adsorption-energy conventions.

**Operational heuristics**

1. Record whether the label is a total configuration energy, formation/adsorption
   energy, atomization energy, or a residual after element references. Bind the actual
   elemental-reference vector and derivation, not only a phrase such as “MP style”.
2. Use one DFT/protocol convention per training head/task. If offsets differ, choose a
   reviewed multihead/multitask design or separate datasets; do not ask one scalar
   target to average incompatible zeros.
3. Evaluate both total-energy and per-atom residual errors when system sizes vary.
   Keep energy differences important to the application as predeclared slices.

### Forces

**Official fact**

MACE, NequIP integrations, and FairChem calculators expose forces derived from model
energy for their energy-conserving routes. Provider data readers still require exact
field names and unit conventions.

**Operational heuristics**

- Verify `F = -dE/dR` with a finite-difference fixture before training or deployment.
  A parser that accepts a force array cannot detect a global sign inversion.
- Freeze whether force metrics are per component, vector norm, per atom, or per frame.
  Report tails and chemically relevant slices as well as a global component MAE.
- If dynamics is intended, require continuous forces under small coordinate changes
  and include high-force/short-distance configurations within the accepted domain.

### Stress and virial

**Official facts**

- MACE can read stress or virial through separate keys and supports configuration-level
  label weights for heterogeneous data.
- NequIP follows dataset units and its ASE calculator exposes explicit energy/length
  conversion factors. ASE/LAMMPS integration adds its own stress representation.
- FairChem fine-tuning distinguishes `e`, `ef`, and `efs`; selecting `efs` requires
  accepted stress labels. Gradient availability after energy-only training is not
  evidence of stress accuracy.

**Operational heuristics**

- Bind tensor order, sign, volume factor, pressure/stress convention, and unit. Test
  the exact converter with a strained periodic fixture and compare all components.
- Do not mix stress and virial as synonymous arrays. Do not authorize cell relaxation
  or NPT from energy/force-only labels or metrics.

## 3. Plan loss, learning rate, checkpoints, and restarts

**Official facts**

- MACE exposes energy/force/stress weights, validation-based stopping, EMA/SWA options,
  and `--restart_latest`; SWA can change target weights late in training.
- NequIP uses Hydra/Lightning configuration. Restarting from `++ckpt_path=...` loads
  the checkpoint model while other dataset/loss/metric/callback settings come from the
  newly supplied config; the provider does not guarantee those changes are safe.
- FairChem v2 writes a canonical Hydra config for a run and its official fine-tuning
  template exposes optimizer, LR scheduler, evaluation cadence, and checkpoint
  callbacks. Hydra `_target_` configs can execute Python code and must be trusted.

**Operational heuristics**

1. Normalize target scales before choosing loss weights. Inspect the contribution of
   each target per batch and per configuration class; prevent atom-rich or force-heavy
   frames from dominating invisibly.
2. Tune using validation only. Freeze model selection, early-stopping rule, seeds,
   precision/device, LR schedule, maximum steps/epochs, checkpoint cadence, and target
   thresholds before reading test/OOD.
3. Run a short data/gradient/checkpoint pilot first. Block on non-finite loss or
   gradients, empty/missing targets, silent unit conversion, irreproducible frame order,
   validation absence, or output-directory collision.
4. Call an operation a restart only when scientific lineage is unchanged. Bind the
   exact checkpoint, optimizer/scheduler state, resolved config, dataset, environment,
   last completed step, and new output root. Compare LR and metrics immediately before
   and after resumption.
5. A changed dataset, loss, architecture, head/task, reference energy, or frozen layer
   set is fine-tuning/new training, not restart. Preserve the parent artifact and run.

## 4. MACE 0.3.16 and foundation-model heads

**Official facts**

- The registered release provides `mace_run_train`, `mace_eval_configs`, and
  `MACECalculator`. The rolling first-party docs describe default data keys, explicit
  energy/force/stress/virial keys, E0s, validation/early stopping, checkpoints, dtype,
  and device selection.
- Current official docs describe naive fine-tuning, multihead replay fine-tuning, and
  LoRA. Fine-tuning is marked experimental; multihead replay is intended to reduce
  catastrophic forgetting. Replay labels may be original DFT labels or base-model
  predictions and therefore have different epistemic meaning.
- A multihead model requires an explicit inference head. The calculator accepts a
  head selection; a target head and replay/pretraining head must not be confused.
- Foundation models differ in elements, training data, DFT level, target system,
  outputs, release requirement, and license. For example, the current model index
  labels MACE-MDP as a dipole/polarizability model, not an energy/force potential.

**Operational heuristics**

- Resolve the model card and exact artifact SHA-256 instead of relying on a convenience
  name whose default can change. Record selected head and head-specific E0s/units.
- For naive fine-tuning, test catastrophic forgetting on a frozen base-domain suite.
  For replay, treat replay frames as training data and keep independent target and
  base-domain test/OOD sets. Distinguish true-DFT replay from self-labeled replay.
- Recompute or explicitly inherit compatible E0s under the target reference protocol.
  A large initial energy offset is a reference-convention alarm, not a reason to
  increase epochs blindly.
- Package/deploy only the intended head and regression-test it against the training
  calculator. The current exact MACE LAMMPS export recipe remains blocked in the
  machine catalog until a version-bound native contract exists.

## 5. NequIP 0.19.0 packages and fine-tuning

**Official facts**

- NequIP distinguishes checkpoints (`.ckpt`), portable packages (`.nequip.zip`), and
  compiled inference artifacts (`.nequip.pth` or `.nequip.pt2`). Compilation target
  and device matter; AOTInductor integration targets include ASE and LAMMPS routes.
- Packaged pretrained models can be used with `ModelFromPackage`. The documentation
  requires the neighbor-list cutoff to match the pretrained model and warns that
  checkpoints from package-based training retain a path dependency on that package.
- Fine-tuning can modify per-type shifts/scales for changed DFT settings. A package may
  contain code and remains an untrusted executable/serialized artifact until reviewed.

**Operational heuristics**

- Copy an accepted package to a stable immutable path before starting and bind its
  hash, metadata, license, code/dependency environment, type mapping, cutoff, units,
  outputs, and reference shifts. Do not move it between restart and packaging.
- Freeze the resolved Hydra config and diff every restart/fine-tune override. Preserve
  target tests and base-domain regression suites.
- Compile on a deployment-like device/toolchain and for the exact integration target.
  Compare checkpoint/package/compiled predictions on identical PBC/type-mapped
  fixtures; repeat for dtype/device changes.
- LAMMPS routes differ: message-passing `pair_nequip` has different rank/scaling limits
  from strictly local Allegro or ML-IAP. Do not infer one provider integration from
  another model's successful compile.

## 6. FairChem v1/v2 and UMA task routing

**Official facts**

- FairChem v2 is a breaking rewrite; v1 `OCPCalculator` and legacy artifacts are not
  v2 APIs. The registered v1 EquiformerV2 profile remains a separate environment.
- UMA uses a single output head with mixture-of-linear-expert routing and requires an
  explicit task input. The task selects the dataset/DFT embedding; for example `omat`
  targets OMat24-style inorganic materials, while `omol` targets molecular data and
  requires charge plus spin multiplicity. `oc22` and `oc25` are UMA-1.2-only tasks in
  the current official guide.
- Official UMA weights are gated. Model repository identity, exact downloaded bytes,
  license/acceptable-use terms, and geographic/access conditions are separate from
  the MIT software license.
- Current FairChem docs describe single-task UMA fine-tuning from ASE-LMDB data with
  regression modes `e`, `ef`, or `efs`; multi-task fine-tuning is not the supported
  convenience route. The current deterministic matrix nevertheless permits only
  pretrained evaluation for `fairchem-v2-uma`.

**Operational heuristics**

- Treat `task_name` as part of model identity. Do not choose it merely because the
  composition fits; match application domain, periodicity, DFT level, dispersion,
  pseudopotentials, charge/spin behavior, and energy reference.
- For `omol`, bind charge and spin multiplicity to every structure. For other tasks,
  preserve the documented fixed/default charge-spin limitations and treat charged,
  magnetic, solvent, oxide, surface, or MOF extrapolations according to the task card.
- Never compare energies across UMA tasks or against Materials Project/legacy OC20
  values without an explicit compatible reference transformation.
- Fine-tuning YAML is executable configuration. Review every `_target_`, use exact
  base-model bytes and one task, freeze canonical config, and keep the provider route
  blocked until the generic schema/evaluator and native regression are promoted.

## 7. Cross-provider fine-tuning gate

Before any fine-tune handoff, require all of:

1. exact base artifact, model card, provider version, license/access, outputs, species,
   cutoff/receptive field, precision, units, and reference convention;
2. target dataset provenance, group-disjoint train/validation/test/OOD, compatible
   labels, and documented domain difference from the base model;
3. explicit strategy: full, frozen layers, LoRA/adapter, naive, replay, or multihead;
4. trainable/frozen parameter inventory, head/task identity, new reference shifts,
   LR/loss/stopping/checkpoint plan, and immutable parent lineage;
5. independent target-domain and base-domain tests for accuracy, tails, conservation,
   stability, catastrophic forgetting, and deployment compatibility.

Passing metadata does not authorize loading the parent model or executing training.

## 8. Frequent failure modes

| Failure | Misleading symptom | Response |
|---|---|---|
| Incompatible energy zero/E0s | Force errors improve while energy offset stays large | Rebuild the reference convention; do not tune against the test set |
| Force sign or unit error | Loss is finite but gradients fight labels | Verify finite differences and converter units on a tiny fixture |
| Stress/virial mix | Tensor shapes pass and cell relaxation looks smooth | Reconstruct sign/volume/order and repeat periodic regression |
| Wrong MACE head or UMA task | Finite plausible predictions | Block and bind the exact head/task plus model card/reference method |
| NequIP cutoff/package moved | Restart or compile fails later | Restore immutable package path and exact cutoff; start new lineage if changed |
| Test reused for model choice | Excellent reported test metric | Invalidate independence and reserve a new test set |
| Naive fine-tune forgets base domain | Target validation improves | Add base-domain regression/replay under a new frozen plan |
| Serialized/YAML artifact untrusted | File has an official-looking extension | Refuse load; verify provenance, code, license, hash, and authorization |

This playbook is content guidance only. It does not change lifecycle, claim ceiling,
provider matrix, execution authorization, or native validation state.
