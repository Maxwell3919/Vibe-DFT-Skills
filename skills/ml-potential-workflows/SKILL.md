---
name: ml-potential-workflows
description: Design and audit fail-closed machine-learned interatomic-potential datasets, grouped train/validation/test splits, provider-bound training plans, model lineage, independent evaluation, and deployment envelopes. Use for MACE, NequIP, GemNet-OC, EquiformerV2, or FairChem UMA workflow planning and evidence review; this development Skill never trains or loads a model and never treats low error metrics alone as deployment evidence.
---

# Machine-learned potential workflows

Read [the local official-manual cache route](references/manual-cache-route.md) before using any external framework, dataset, or model documentation body.

This is a **development, non-routable Skill**. It makes dataset, split, training,
evaluation, and deployment assumptions explicit for a fast or low-reasoning model.
It does not import a provider framework, load a model archive, start training, run
inference, or approve deployment. Every report stays at
`claim_ceiling=no_positive_claim` until atomic promotion.

## Required reads

1. [Fail-closed contract](references/fail-closed-contract.md)
2. [Dataset and leakage rules](references/dataset-and-leakage.md)
3. [Provider capability matrix](references/provider-matrix.md)
4. [Training and transfer playbook](references/training-and-transfer.md) for provider
   selection, reference energy/force/stress conventions, loss/LR/checkpoint planning,
   foundation-model heads/tasks, and fine-tuning. Preserve its explicit separation of
   official facts from operational heuristics.
5. [Evaluation and deployment rules](references/evaluation-and-deployment.md),
   including domain shift, calibrated uncertainty, adapter compatibility, MD pilots,
   and failure response.
6. [Official-source boundary](references/official-sources.md)
7. [Task evidence profiles](references/task-evidence-profiles.json)
8. [Weak-model decision table](references/weak-model-decision-table.json) whenever
   selecting an action state or minimum next action; interpret it as
   `candidate-decision-table@1.0`, evaluate increasing `priority`, stop at the first
   match, and use the final fail-closed `default_case_id` if no earlier row matches
   uniquely. Never infer execution or promotion authorization
9. [Exact provider workflow catalog](references/provider-workflow-catalog.json) for
   MACE 0.3.16, NequIP 0.19.0, FairChem v1 1.10.0, and FairChem v2 2.21.0.
10. [Calling and recipe boundary](references/calling-and-recipes.md) plus exactly one
   entry from [provider recipes](references/provider-recipes.json) before describing
   a native CLI/API handoff. Every recipe is unauthorized and native-not-run.
11. [Official-document pack seed](references/source-pack-seed.json) together with its
    hash-bound [scope catalog](references/source-pack-scope-catalog.json) before any
    source-completeness statement. The seed is deliberately `blocked`: every provider
    input is metadata-only and no official page body, checkpoint, or dataset is
    bundled.
12. [Central authority proposal](references/source-pack-authority-proposal.json) only
    as a machine-readable review request. It neither activates a registry authority
    nor raises this Skill's lifecycle or claim ceiling.

## Official-document pack state

The offline maintenance extractor splits seven authorities: exact MACE framework
source, version-divergent MACE docs, exact NequIP source/docs, FairChem v1, FairChem
v2, gated UMA model metadata, and FairChem dataset/reference-protocol documentation.
Check deterministic regeneration with:

```bash
python3 -B skills/ml-potential-workflows/scripts/extract_official_source_scope.py \
  --check
```

This command uses tracked metadata only. It has no network or provider import path
and cannot download, inspect, deserialize, or load a model or dataset. A successful
check proves only that the catalog, hashes, scope and proposal reproduce; it does not
resolve the recorded blockers or authorize central binding.

## Manual-first provider decision

1. Select exact provider, version and operation from the catalog. Do not translate
   configs, checkpoints, packages, task heads or pretrained artifacts across rows.
2. Resolve every `source_id`. Exact tag source establishes console/API surfaces;
   rolling docs are explicitly labeled and must agree with installed help before a
   future native run.
3. Report recipe preconditions, exact entry point, outputs, restart rule, failure
   modes, units and scientific gates. A recipe is a handoff specification only.
4. Apply the generic guard to manifests/lineage. `generic-evidence-only` never means
   provider config validation, safe deserialization, inference or deployment.
5. Report the current `native-not-run` state. No registered provider distribution or
   CLI was present, and no install/import/model load/train/evaluate/compile/download/
   inference probe ran.

Hard version boundaries: NequIP 0.19.0 removed legacy evaluate/deploy commands;
FairChem v2 is incompatible with v1 code/pretrained artifacts; and current Python
3.14 is outside FairChem v1 `>=3.9,<3.13` and v2 `>=3.11,<3.14`. The unresolved
FairChem v1 GemNet-OC and MACE LAMMPS-export recipes remain explicitly blocked.

## Hard boundary

- Never run training, inference, molecular dynamics, a provider CLI, a scheduler,
  arbitrary model code, pickle, or an executable archive.
- Never load a checkpoint or model package merely to inspect metadata. Model archives
  may contain executable or unsafe serialized content.
- Never infer dataset units, species order, DFT protocol, split independence, model
  domain, license, or scientific acceptance from a filename, framework name, plot, or
  prose.
- Framework license, model license, data license, and reference-DFT redistribution
  rights are four independent records.
- A random frame split is not automatically independent. Correlated frames from one
  trajectory, relaxation, structure family, defect series, or perturbation family
  must share a `group_id` and stay in one split.
- Validation data selects settings; test data evaluates the frozen choice. Reusing
  test results for tuning invalidates the independent-test claim.
- Low average MAE/RMSE does not establish low worst-case error, force stability,
  energy conservation, phase transferability, reaction-path validity, or safe MD.
- Provider terms that sound similar are not interchangeable: MACE heads, UMA task
  embeddings, NequIP output fields, and a generic workflow mode have different
  identities and reference conventions.

## Fixed workflow for low-reasoning models

### 1. Classify the terminal intent

Choose one local operation only:

- `audit-dataset`
- `plan-training`
- `audit-model`
- `audit-evaluation`
- `audit-deployment`

If the request is to train, infer, deploy, or launch MD, return
`needs_authorization` only after all preceding local gates pass; this candidate has no
execution action and cannot satisfy that request.

### 2. Audit the dataset inventory

```bash
python3 -B skills/ml-potential-workflows/scripts/mlp_guard.py \
  audit-dataset --manifest dataset.json --out dataset-audit.json
```

The manifest must bind every frame metadata record to exact structure, label,
reference-run, and scientific-acceptance hashes; declare one reference protocol,
species order, units, periodicity class, label coverage, group ID, and split. The
auditor rejects:

- duplicate frame/structure/label identity;
- any group spanning train, validation, and test;
- absent train, validation, or test split;
- mixed units, protocol hashes, or species outside the type map;
- missing energy/force labels or inconsistent stress coverage;
- missing source-run or source-acceptance hashes;
- non-finite statistics or unsafe identifiers;
- test-use policy other than `held_out_once_after_freeze`.

A pass proves only that the manifest metadata is internally consistent. It does not
resolve or authenticate the referenced frame bytes.

### 3. Freeze a provider-bound training plan

```bash
python3 -B skills/ml-potential-workflows/scripts/mlp_guard.py \
  plan-training --request training-request.json \
  --dataset-audit dataset-audit.json --out training-plan.json
```

Require exact provider profile/version, workflow mode, dataset-audit hash, species
order, random seeds, precision, cutoff, loss terms/weights, stopping rule, checkpoint
policy, target metrics and tolerances, evaluation slice categories plus exact
predeclared slice IDs, and environment identity.
Do not fill provider defaults. The provider matrix separates trainable-framework
profiles from pretrained-evaluation profiles.

Before freezing a plan, use `training-and-transfer.md` to resolve reference energies,
force sign, stress/virial convention, provider-specific head/task, checkpoint mode,
and fine-tuning parent. Narrative provider support never expands the combinations
accepted by the current deterministic matrix.

### 4. Audit model lineage without loading the model

```bash
python3 -B skills/ml-potential-workflows/scripts/mlp_guard.py \
  audit-model --manifest model.json --training-plan training-plan.json \
  --out model-audit.json
```

Require exact artifact hash/bytes, provider/revision, immutable dataset and plan
references, training-run hash, species order, units, cutoff, precision, energy
reference convention, framework/model/data licenses, and training status. A
pretrained model instead requires an official model identity, published domain,
artifact hash, model-card hash, and independent license attestation. The tool never
opens the artifact.

### 5. Audit independent evaluation

```bash
python3 -B skills/ml-potential-workflows/scripts/mlp_guard.py \
  audit-evaluation --evaluation evaluation.json --model-audit model-audit.json \
  --dataset-audit dataset-audit.json --training-plan training-plan.json \
  --out evaluation-audit.json
```

Require exact model/dataset/plan lineage, held-out test status, per-target units,
MAE/RMSE/max or high-quantile errors, per-species/configuration slices, OOD set,
force/stress coverage when targeted, deterministic evaluator identity, and every
predeclared threshold. Missing a worst-case or OOD result cannot be hidden by a low
mean error.

### 6. Audit a deployment envelope

```bash
python3 -B skills/ml-potential-workflows/scripts/mlp_guard.py \
  audit-deployment --deployment deployment.json \
  --evaluation-audit evaluation-audit.json --model-audit model-audit.json \
  --out deployment-audit.json
```

Require exact model/evaluation hashes, target engine/version, species and unit match,
supported observable set, thermodynamic/structural domain, timestep/ensemble boundary,
extrapolation monitor, fail action, rollback identity, trial budget, and explicit
execution authorization reference. A local pass remains a handoff candidate; it is
not permission to deploy.

### 7. Respond canonically

Return:

1. `route=ml-potential-workflows`
2. one action state from `local_gate_blocked`, `needs_evidence`,
   `needs_authorization`, `handoff_ready`, `local_gate_passed_limited`
3. `claim_ceiling=no_positive_claim` while in development
4. passed gates
5. stable blocking finding codes
6. smallest next action
7. safe evidence labels and SHA-256 values
8. explicit limitations

Natural-language assertions can lower the state but never raise it.

## Provider separation

The registry currently plans MACE, NequIP, GemNet-OC, EquiformerV2, and FairChem UMA
profiles. They are not interchangeable. Provider-specific configuration validation,
dependency matrices, model packaging, pretrained weights, and execution adapters must
remain separate from this generic evidence layer. DeePMD-kit is owned by the separate
`deepmd-rigorous-workflows` candidate.

The catalog provides real documented entry points without claiming support:
`mace_run_train`/`mace_eval_configs`/`MACECalculator`, NequIP's
`nequip-train`/`nequip-package`/`nequip-compile`, FairChem v1 `OCPCalculator`, and
FairChem v2 `pretrained_mlip` plus `FAIRChemCalculator`. Checkpoints, `.model`,
`.nequip.zip`, `.pt2`, and provider model caches are untrusted executable/serialized
artifacts until an external platform establishes provenance and authorizes loading.

## Handoff boundary

The planned `ml-dataset-manifest`, `ml-training-plan`, `ml-training-run`,
`ml-evaluation-manifest`, `ml-model-manifest`, `ml-deployment-manifest`, and
`ml-inference-run` interfaces have no production schemas/evaluators yet. Candidate
reports are precursors and cannot be emitted as live cross-Skill contracts. Promotion
requires schema/evaluator closure, exact provider adapters, legal real artifacts,
independent test and OOD evidence, installer coverage, and weak-model blind tests in
one reviewed delta.
