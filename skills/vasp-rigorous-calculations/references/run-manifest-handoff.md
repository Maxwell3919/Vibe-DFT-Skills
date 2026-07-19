# VASP run-manifest handoff

Emit the canonical repository `contracts/run-manifest.schema.json` immutable pre-decision record at every technical terminal event: completion, intentional stop, failure, or abandonment. Encode deliberate abandonment as `stopped` with an explicit limitation, or as `failed` when the application actually failed; never invent an `abandoned` status.

- Use an anonymized `case_id` and stable `scientific_protocol_id`.
- Record VASP version, task type, technical status, pre-decision review readiness, configuration, observed metrics, evidence labels/checksums, and limitations.
- Attach the schema-2.0 VASP audit SHA-256 and preserve every non-pass gate as a limitation. Do not copy its local filesystem path.
- Use `status=completed` with `scientific_acceptance=not_assessed` or `requires_human_review`; every noncompleted status must remain `not_assessed`.
- A convergence candidate may support only its emitted observable/tolerance evidence label. Never write accepted/rejected into this manifest or rewrite it after review; use the downstream calculation record, human decision, and post-decision claim map.
- Do not include POTCAR contents, private absolute paths, hosts, accounts, project names, or unpublished material identifiers.
- Route outputs to `dft-postprocess`; route the terminal manifest and scheduler metrics to `dft-campaign-efficiency`.
- A manifest records evidence; it does not itself prove completion, convergence, task validity, or physical validity. Never use manifest field values to override a blocked auditor gate.
