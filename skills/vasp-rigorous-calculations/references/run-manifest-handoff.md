# VASP run-manifest handoff

Emit the canonical repository `contracts/run-manifest.schema.json` record at every terminal event: completion, intentional stop, failure, abandonment, or scientific acceptance.

- Use an anonymized `case_id` and stable `scientific_protocol_id`.
- Record VASP version, task type, status, acceptance, configuration, observed metrics, evidence labels/checksums, and limitations.
- Attach the schema-2.0 VASP audit SHA-256 and preserve every non-pass gate as a limitation. Do not copy its local filesystem path.
- Keep `scientific_acceptance=not_assessed` when only input gates or technical run gates pass.
- A convergence candidate may support only its emitted observable/tolerance evidence label. It does not authorize `scientific_acceptance=accepted` without task-specific and physical/model validation.
- Do not include POTCAR contents, private absolute paths, hosts, accounts, project names, or unpublished material identifiers.
- Route outputs to `dft-postprocess`; route the terminal manifest and scheduler metrics to `dft-campaign-efficiency`.
- A manifest records evidence; it does not itself prove completion, convergence, task validity, or physical validity. Never use manifest field values to override a blocked auditor gate.
