---
name: deepmd-rigorous-workflows
description: Design and audit fail-closed DeePMD-kit 3.1.3 dataset-layout manifests, portable training-config projections, technical training-run records, and frozen-model lineage across explicit backends. Use for DeePMD type-map, array-shape, split, seed, descriptor, fitting, loss, checkpoint, and reproducibility evidence; this development Skill never imports DeePMD, reads NumPy payloads, trains, freezes, tests, or deploys a model.
---

# DeePMD rigorous workflows

This Skill is in development and non-routable. It adds a provider-specific evidence
layer beneath the generic `ml-potential-workflows` rules. It never imports DeePMD-kit,
TensorFlow, PyTorch, JAX, Paddle, NumPy, dpdata, or LAMMPS; never reads array/model
payloads; and never executes `dp train`, `dp freeze`, `dp test`, or inference.

All reports remain `claim_ceiling=no_positive_claim` until the Skill, interfaces,
environment adapter, and real-artifact tests are atomically promoted.

## Required reads

1. [Fail-closed contract](references/fail-closed-contract.md)
2. [Dataset layout contract](references/dataset-layout.md)
3. [Training projection contract](references/training-projection.md)
4. [Run and model lineage](references/run-and-model-lineage.md)
5. [Official-source and backend boundary](references/official-sources.md)
6. [Task evidence profiles](references/task-evidence-profiles.json)
7. [Weak-model decision table](references/weak-model-decision-table.json) whenever
   selecting an action state or minimum next action; interpret it as
   `candidate-decision-table@1.0`, evaluate increasing `priority`, stop at the first
   match, and use the final fail-closed `default_case_id` if no earlier row matches
   uniquely. Never infer execution or promotion authorization
8. [Provider workflow catalog](references/workflow-catalog.json) for discoverable
   DeePMD-kit 3.1.3, dpdata 1.0.2, and DP-GEN 0.13.3 operations. `listed` means only
   first-party documented.
9. [Calling boundary](references/calling-and-recipes.md) and the selected exact entry
   in [workflow recipes](references/workflow-recipes.json) before describing any
   native CLI/API handoff. Every recipe remains unauthorized and native-not-run.

## Manual-first provider decision

1. Match provider, exact version, operation and backend in `workflow-catalog.json`.
2. Resolve all `source_ids`; prefer exact versioned docs/releases and label rolling
   dpdata docs explicitly.
3. Select one recipe and report its preconditions, outputs, restart rule, failure
   modes, units and scientific checks without running it.
4. Apply the deterministic guard only to its implemented offline manifests. Catalog
   membership and a provider recipe do not expand guard support.
5. Keep the current native state `native-not-run`: no `dp`, `dpdata`, or `dpgen`
   executable/distribution was present, so no help, import, conversion, training,
   inference or installation probe ran.

The actual PyTorch CPU install route is separate from the documented
`deepmd-kit[cpu]` TensorFlow CPU extra. The registered recipe installs PyTorch first,
then pins `deepmd-kit==3.1.3`, captures `dp --version` and `dp --pt -h`, and freezes
the resolved compatible dependency lock. Never use the implicit TensorFlow backend
for a PyTorch plan.

## Hard boundary

- The registered target is DeePMD-kit `3.1.3` CPU with an explicit backend. Backend
  interchangeability is not assumed.
- Training projections accept only the version-matched `pytorch`, `tensorflow`, or
  `paddle` backends. A `jax` layout may be inventoried, but it cannot pass the current
  training-config gate; the reference `dp` backend is not registered at all.
- Dataset metadata, raw array bytes, portable system IDs, private paths, training
  projection, rendered DeePMD config, environment, run, checkpoint, frozen model,
  evaluation, and deployment are distinct evidence.
- Hashes in a manifest do not prove that referenced files exist or have valid NumPy
  headers. A future trusted adapter must resolve and inspect exact bytes.
- A `type_map` index mismatch can silently change chemistry; any mismatch blocks.
- Frames derived from the same trajectory/relaxation/query group stay in one split.
- Validation controls training decisions; test and OOD sets remain independent.
- A completed training step count or low learning-curve error does not prove an
  accurate, stable, transferable, or deployable potential.
- Framework license does not establish backend, model, dataset, or reference-data
  license rights.

## Mechanical workflow

### 1. Audit a portable dataset-layout manifest

```bash
python3 -B skills/deepmd-rigorous-workflows/scripts/deepmd_guard.py \
  audit-layout --manifest layout.json --out layout-audit.json
```

The manifest declares exact DeePMD version/backend, ordered `type_map`, energy/force/
virial units, reference-protocol hash, system groups and split roles. Each system
declares `nframes`, `natoms`, `type.raw`/`type_map.raw` hashes and the exact hash,
dtype and shape of required arrays. It also binds the generic dataset audit and an
ordered row-to-source index for each system. The checker never opens those arrays or
source indices.

Require nonempty train, validation, test and OOD systems; group-disjoint splits;
unique system and array identity; consistent type-map hash; `coord`, `energy`, and
`force` shapes; `box` for periodic systems; and uniform virial coverage.

### 2. Audit a portable training projection

```bash
python3 -B skills/deepmd-rigorous-workflows/scripts/deepmd_guard.py \
  audit-config --projection training-projection.json \
  --layout-audit layout-audit.json --out config-audit.json
```

The projection is deliberately not an executable provider config. It freezes:

- exact version, backend, environment and layout-audit hashes;
- ordered type map and safe train/validation system IDs;
- descriptor type/cutoff/smoothing/selection/network/seed;
- energy fitting network/seed;
- explicit learning-rate schedule;
- energy/force/virial loss weights;
- training seed, step count, display/checkpoint cadence and batch sizes;
- checkpoint restart parent and exact provider-schema evidence hash;
- predeclared evaluation metrics and thresholds.

No field is filled from a DeePMD default. A future version-bound adapter must render
private filesystem paths and validate the rendered config against the official
provider schema produced by the exact installed `dp` tool.

### 3. Audit a technical training-run record

```bash
python3 -B skills/deepmd-rigorous-workflows/scripts/deepmd_guard.py \
  audit-run --record training-run.json --config-audit config-audit.json \
  --layout-audit layout-audit.json --out run-audit.json
```

Require exact version/backend/environment/layout/config hashes, authorized execution
record hash, zero exit code, completed final step, checkpoint and learning-curve
hashes, finite train/validation metrics in exact units, no non-finite sentinel, and
restart-parent consistency. The checker does not read logs or checkpoints; a future
adapter must produce the record from exact execution artifacts.

### 4. Audit a frozen-model manifest

```bash
python3 -B skills/deepmd-rigorous-workflows/scripts/deepmd_guard.py \
  audit-model --manifest model.json --run-audit run-audit.json \
  --config-audit config-audit.json --out model-audit.json
```

Require exact frozen-model hash/bytes, run/config lineage, version/backend, type map,
cutoff, units, energy convention, generic source-dataset audit, provider
config/schema hashes and separate
framework/backend/model/dataset licenses. The tool never loads the model.

### 5. Hand off to generic evaluation

Only after both candidates are promoted may a model audit feed
`ml-potential-workflows` independent-test/OOD/deployment gates. This candidate does
not claim inference accuracy or deployment readiness from training metrics.

### 6. Canonical answer

Return:

1. `route=deepmd-rigorous-workflows`
2. `action_state` from `local_gate_blocked`, `needs_evidence`,
   `needs_authorization`, or `local_gate_passed_limited`
3. `claim_ceiling=no_positive_claim`
4. exact passed gates and stable finding codes
5. one smallest next action
6. safe labels and hashes only
7. explicit parser/adapter/scientific limitations

Do not treat a natural-language “training finished” statement as a run record.

## Activation blockers

The current machine lacks DeePMD-kit and supported backend evidence. Promotion also
requires schemas and semantic evaluators for all planned ML interfaces, a supported
isolated Python environment, exact provider-schema generation, legal real DeepMD data,
train/restart/freeze/test/inference regressions, backend-specific results,
authorization integration, installer coverage, and low-reasoning blind tests.
