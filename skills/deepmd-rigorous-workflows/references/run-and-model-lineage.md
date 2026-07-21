# Run and model lineage

## Technical run

A run record binds exact layout-audit, config-audit, environment, rendered config,
external execution-authorization, execution-record and output-log hashes. Completion
requires a zero exit code, `completed` status, exact planned final step, no non-finite
sentinel, and checkpoint plus learning-curve hashes. Metrics are finite technical
observations, not acceptance.

A restart run binds both the parent checkpoint and parent run audit from the
projection. A from-scratch run forbids restart ancestry. Automatic retry is outside
this candidate.

## Frozen model

A model manifest binds exact run/config reports and the run checkpoint, then declares
model artifact hash and bytes, version/backend, ordered type map, cutoff, units,
energy reference convention, provider-rendered config hash, provider-schema hash and
separate license identities.

Freezing success does not prove inference equivalence across backends or consumers.
Independent test/OOD metrics, MD stability, adapter identity and deployment envelopes
belong to the generic MLP workflow and engine-specific skills.

Compression is a derived-artifact transformation: bind the uncompressed parent and
repeat exact prediction, held-out/OOD, device/precision, and deployment-adapter
regressions. `dp test --numb-test 0` is the documented all-frame provider route, but a
provider metric file still needs independent frame-count, unit, slice, tail, and
threshold validation. Committee model deviation is an uncertainty signal, not an
error certificate; calibrate it against reference errors before using any threshold.

For LAMMPS, bind the exact consumer build/plugin, unit style, atom-type mapping, model
order, and monitoring configuration. With multiple DeepMD models the first model
drives dynamics while the set supplies deviation, so model order is scientific
lineage. See [provider operational workflow](operational-workflow.md) for the complete
handoff and failure checklist.

DeepMD layout/model metadata records virial in `eV`; the generic workflow records
stress in `eV/angstrom^3`. Handoff therefore requires an explicit, tested
cell-volume/sign/convention conversion adapter bound to exact periodic cell bytes.
Never relabel virial as stress or copy the numeric values unchanged.
