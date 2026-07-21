# DeePMD provider operational workflow

Use this playbook only after the fail-closed dataset and lineage contracts. Every
statement below is labeled either **Official fact** or **Operational heuristic**.
Official facts describe DeePMD-kit 3.1.3 behavior from the sources listed in
[`official-sources.md`](official-sources.md). Operational heuristics are conservative
practitioner guidance; they are not DeePMD defaults, universal numerical thresholds,
or evidence that this Skill ran the provider.

## Contents

1. Dataset construction and units
2. Leakage-safe split rendering
3. Descriptor, loss, and learning-rate planning
4. Checkpoint, restart, and fine-tuning lineage
5. Freeze, compress, and independent test
6. Committee deviation and active learning
7. LAMMPS deployment compatibility
8. Failure modes and minimum response

## 1. Dataset construction and units

**Official facts**

- A standard DeePMD system contains frames with the same atom types and atom count.
  `type.raw` supplies integer atom-type indexes; `type_map.raw` maps those indexes to
  names. NumPy frame properties live under `set.*` directories, while `type.raw`,
  `type_map.raw`, and optional `nopbc` live at the system root.
- Coordinates and boxes use angstrom, energy uses eV, forces use eV/angstrom, and
  virial uses eV. Periodic frames require boxes; an empty `nopbc` marks a
  non-periodic system.
- The logical property shapes are coordinates `[nframe, natom, 3]`, boxes
  `[nframe, 3, 3]`, energies `[nframe]`, forces `[nframe, natom, 3]`, and virials
  `[nframe, 9]`. The version-matched reference `raw_to_set.sh` writes the canonical
  NPY headers as flattened frame rows: coordinates/forces
  `[nframe, 3 * natom]` and boxes/virials `[nframe, 9]`. The tensor component order
  is `XX XY XZ YX YY YZ ZX ZY ZZ`.
- The mixed-type format adds per-frame atom types and is descriptor-limited in the
  3.1.3 manual. Do not select it merely to merge sparse systems.

**Operational heuristics**

1. Convert into a new immutable staging directory. Preserve an ordered
   `frame_id -> source calculation -> source frame -> correlation group` index before
   any shuffle, filtering, deduplication, or `set.*` chunking.
2. Verify each source calculation first: electronic/ionic completion, label units,
   atom order, cell/PBC, energy definition, force sign, virial/stress conversion, and
   reference-method identity. A successful `dpdata` parse proves none of these.
3. Normalize once, then hash. Never mix converted and unconverted labels in one
   system. Keep raw source identity and conversion-tool/version identity separately.
4. Generate one ordered `type_map` for the campaign. Recompute every `type.raw` from
   chemical identity and reject unknown or silently reordered types. Compare the
   rendered map with `dp show ... type-map` after freezing.
5. Treat virial and stress as different quantities. Bind the exact volume, tensor
   order, sign, and convention used by the converter; test the conversion on a small
   periodic fixture before enabling virial loss.
6. Keep physically distinct reference protocols in different dataset versions even
   if their units match. Functional, pseudopotential, cutoff, spin/charge, dispersion,
   energy offset, and convergence policy are part of the label definition.

## 2. Leakage-safe split rendering

**Official fact**

The training input has separate training and validation system lists. `dp test`
evaluates an explicit system later. The `set.*` directories are chunks of one system;
the manual does not define them as train/validation/test partitions.

**Operational heuristics**

- Assign split roles before writing DeePMD systems. Keep all frames from one MD
  segment, relaxation, perturbation parent, active-learning query batch, symmetry
  family, or near-duplicate structure family in one role.
- Render only train systems into `training_data` and only validation systems into
  `validation_data`. Keep held-out test and OOD roots absent from the training config
  so an accidental glob cannot consume them.
- Stratify by the deployment envelope, not frame count alone: composition, phase,
  coordination, density/volume, temperature, pressure/strain, defect/surface class,
  and force/energy tails. Record any uncovered slice as a domain limitation.
- Never tune descriptor, loss, learning rate, step count, or active-learning
  selection threshold against test/OOD results. If that occurs, version a new plan
  and reserve a new independent test set.

## 3. Descriptor, loss, and learning-rate planning

**Official facts**

- DeePMD 3.1.3 provides `neighbor-stat`; descriptor `sel` is type ordered and depends
  on the selected cutoff and dataset.
- For an energy model, energy, force, and virial loss prefactors have start and limit
  values. A target is ignored only when both of its prefactors are zero; nonzero
  weights require the corresponding labels.
- Version 3.1.3 requires `start_lr` plus exactly one of `stop_lr` or
  `stop_lr_ratio`. It documents exponential and cosine schedules and optional warmup.
- The quick-start tutorial shows force-dominant early weighting and larger relative
  energy weight late in training. That is a tutorial strategy, not a validated value
  for another dataset.

**Operational heuristics**

1. Run neighbor statistics over every train system for each candidate cutoff. Add
   recorded headroom to observed neighbor counts and fail if production pilots exceed
   the selected capacity. Converge cutoff/selection against target observables and
   cost; do not copy tutorial `rcut` or `sel`.
2. Inspect energy-per-atom, force-component/norm, and virial distributions by slice.
   Choose loss weights so that one target does not dominate solely through atom count,
   unit scale, or rare extreme labels. Predeclare the schedule and compare per-target
   validation curves, not total loss alone.
3. Use virial loss only when every included periodic system has accepted virials and
   pressure/cell behavior is a deployment target. Otherwise freeze both virial
   prefactors to zero.
4. Start with a bounded pilot that exercises data loading, validation, checkpointing,
   and loss finiteness. Scale to the planned run only after the pilot reproduces with
   the same rendered config and environment.
5. Choose LR schedule, warmup, and total steps together. Record the actual final LR,
   gradient/non-finite events, train/validation gap, and whether validation improves
   after each loss-weight transition. Extend training only under a new frozen plan.
6. Train multiple independent initializations when uncertainty or active learning is
   required. Reusing the same seed or checkpoint does not form an independent
   committee.

## 4. Checkpoint, restart, and fine-tuning lineage

**Official facts**

- `dp ... train INPUT --restart CHECKPOINT` resumes from a checkpoint.
- `--finetune PRETRAINED_MODEL` is a distinct operation. In the PyTorch 3.1.3 route,
  the pretrained model constrains model structure; documented options can reuse the
  pretrained script/model branch. The manual warns that datasets or upstream
  computational settings can introduce energy shifts.

**Operational heuristics**

- Call an operation a restart only when dataset bytes, type map, provider/backend,
  model structure, loss, LR schedule, seeds, and scientific intent remain identical.
  Bind the exact checkpoint family and last completed step; preserve parent outputs.
- After restart, check step, optimizer/LR, and loss continuity. A zero exit code with
  a reset scheduler or wrong checkpoint is a new run, not a valid continuation.
- Treat any new data, new label protocol, changed type set, changed loss, or changed
  architecture as a new plan. If a pretrained model is used, record parent artifact,
  model metadata, license, type map, reference protocol, and what was frozen or
  reinitialized. This candidate guard does not yet validate fine-tuning.

## 5. Freeze, compress, and independent test

**Official facts**

- `freeze`, `compress`, and `test` are separate provider operations. Backend-specific
  artifacts differ; the 3.1.3 CLI documents `.pth` for PyTorch frozen models.
- `dp test --numb-test 0` evaluates all frames and can write detailed energy, force,
  and virial results. Compression creates a derived model rather than updating the
  source model in place.

**Operational heuristics**

1. Freeze a selected checkpoint to a new path; capture artifact hash, byte count,
   `dp show` metadata, provider/backend/environment, and parent checkpoint/run.
2. Compare checkpoint and frozen-model predictions on a fixed accepted fixture before
   using held-out data. Then run all held-out frames and independently compute
   predeclared MAE/RMSE/tail/slice/OOD metrics from detailed predictions.
3. Accept a compressed model only after repeating prediction-equivalence, held-out,
   OOD, device/precision, and deployment-adapter regression. Keep both source and
   compressed identities; never report the source model's metrics for the compressed
   artifact.
4. Block on non-finite predictions, missing frames, unexplained type-map/cutoff drift,
   force-energy inconsistency, or a result file that cannot be bound to exact input
   and model bytes.

## 6. Committee deviation and active learning

**Official fact**

DeePMD model deviation is the ensemble standard deviation of predicted forces or
virials from independently initialized models trained on the same data. The CLI can
report absolute or relative deviation; LAMMPS can use multiple models while the first
model supplies dynamics and the ensemble supplies deviation output.

**Operational heuristics**

- Calibrate deviation against real reference errors on a separate calibration set.
  A threshold copied from another chemistry, model family, unit convention, or force
  scale is not transferable.
- Track maximum atomic force deviation plus distribution/slice summaries. Low
  committee spread can still be confidently wrong because all members share data,
  architecture, or reference bias.
- Select new labels from the exploration pool without consulting held-out test/OOD.
  Preserve rare environments and high-error tails; do not let dense equilibrium
  frames crowd out chemically important events.
- Stop exploration on non-finite predictions, broken topology, extreme geometry,
  unbounded deviation, or a configured physical sentinel. Record the frame before
  labeling; do not silently continue past the model domain.

## 7. LAMMPS deployment compatibility

**Official facts**

- `pair_style deepmd` consumes one or more frozen models. With multiple models, the
  first supplies energy/forces and the others contribute to model deviation.
- `pair_coeff * * ...` maps LAMMPS atom types to model atom names. The mapping can use
  the model `type_map`; explicit `NULL` values are for hybrid styles.
- DeePMD-kit 3.1.3 documents all LAMMPS unit styles except `lj`; `metal` matches its
  internal angstrom/eV/eV-per-angstrom convention.

**Operational heuristics**

1. Bind exact LAMMPS version/build, DeePMD plugin/library, model artifact, species
   mapping, unit style, neighbor settings, precision/device, and model-deviation
   output cadence. Library compatibility is separate from Python training success.
2. Compare the same periodic fixtures through `dp test` or Python inference and the
   target LAMMPS build. Check energy, every force component, virial/stress convention,
   PBC images, and atom-type permutation before MD.
3. Start with bounded minimization and short low-risk NVE/NVT pilots. Check force
   continuity, energy drift where applicable, temperature/pressure behavior, minimum
   distances, coordination, model deviation, and deterministic stop/rollback.
4. Do not begin NPT or claim pressure behavior without accepted virial/stress labels,
   independent stress metrics, and cell-response pilots.

## 8. Failure modes and minimum response

| Failure | Why it can look successful | Minimum response |
|---|---|---|
| Type-map permutation | Training/inference remains finite with wrong chemistry | Block; rebuild types and every descendant artifact |
| Correlated frame split | Random-frame metrics look unusually good | Regroup by source lineage and reserve a new test set |
| Mixed reference protocol | Loss may converge to an average offset | Separate dataset versions or define a reviewed multi-task route |
| Virial/stress confusion | Shapes and units may still parse | Reconstruct conversion with cell/sign/tensor evidence |
| Neighbor capacity/cutoff gap | Train data never triggers the missing environment | Expand/converge coverage and rerun OOD/deployment pilots |
| Restart from wrong checkpoint | Step count continues and exit code is zero | Reject lineage; preserve outputs and start a correctly bound run |
| Compression/backend drift | Derived artifact loads normally | Re-evaluate exact derived bytes across targets and devices |
| Low committee spread OOD | Members share the same blind spot | Add calibrated physics/domain sentinels and reference labels |
| LAMMPS map/unit/plugin mismatch | MD can run for many steps | Stop, compare fixed fixtures, and rebuild the deployment record |

None of these checks authorizes native training, model loading, inference, or MD in
the current development Skill.
