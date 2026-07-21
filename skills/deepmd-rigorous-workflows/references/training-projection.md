# Training projection contract

The portable projection is an evidence record, not a DeePMD input file. It contains
no filesystem paths. A trusted version-bound adapter later maps system IDs to private
paths and validates the rendered provider config with a schema emitted by the exact
installed DeePMD tool.

Initial descriptor profile: `se_e2_a` with explicit `rcut`, `rcut_smth`, per-type
neighbor selection, hidden neurons, axis neurons and seed. Initial fitting profile:
energy fitting with explicit hidden neurons, residual toggle and seed. Other
descriptors/fittings require independent profiles.

Learning rate, every loss start/limit weight, training seed, number of steps,
display/save cadence, train/validation batch size, provider schema hash and evaluation
thresholds are mandatory. Backend and version are exact. Backend translation is not
performed. For DeePMD-kit 3.1.3 this training projection accepts only explicit
`pytorch`, `tensorflow`, or `paddle`; a JAX layout may be inventoried but cannot be
turned into a training projection because the version-matched provider documentation
does not register JAX training. Display and checkpoint cadences cannot exceed the
total planned step count; otherwise the projection cannot support the promised
trace/checkpoint record.

The portable loss keys map to provider `start_pref_e`/`limit_pref_e`,
`start_pref_f`/`limit_pref_f`, and `start_pref_v`/`limit_pref_v` only through a
version-bound renderer. Nonzero provider weights require corresponding labels.
Tutorial weight schedules are examples and must not be copied as scientific defaults.

For 3.1.3, render an explicit `start_lr` and exactly one of `stop_lr` or
`stop_lr_ratio`, plus the schedule type and every applicable decay/warmup field. The
provider documents exponential and cosine schedules. This initial projection models
only its registered schedule fields; any future cosine/warmup profile requires a
schema and fixture extension rather than silent omission.

Restart requires distinct parent checkpoint and parent run-audit SHA-256 values.
From-scratch mode forbids both. The parent report remains unsigned metadata until a
trusted resolver verifies its exact checkpoint, dataset, config, backend and version.
Changing dataset, type map, descriptor shape, fitting shape, backend or version
creates a new plan; it is not a transparent restart.

Fine-tuning is also not restart. The 3.1.3 provider documents backend-specific
`--finetune` behavior, inherited model structure, and energy-bias handling, but this
candidate has no fine-tuning projection or evaluator. Record it as an unsupported
new lineage until those contracts exist. Use [provider operational workflow](operational-workflow.md)
for the practical decision checklist.
