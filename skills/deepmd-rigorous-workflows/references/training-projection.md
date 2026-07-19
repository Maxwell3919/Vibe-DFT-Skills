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
does not register JAX training. Display and checkpoint cadences cannot exceed the total planned step
count; otherwise the projection cannot support the promised trace/checkpoint record.

Restart requires distinct parent checkpoint and parent run-audit SHA-256 values.
From-scratch mode forbids both. The parent report remains unsigned metadata until a
trusted resolver verifies its exact checkpoint, dataset, config, backend and version.
Changing dataset, type map, descriptor shape, fitting shape, backend or version
creates a new plan; it is not a transparent restart.
