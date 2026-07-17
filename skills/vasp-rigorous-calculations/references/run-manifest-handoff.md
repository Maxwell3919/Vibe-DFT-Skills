# VASP run-manifest handoff

Emit the canonical repository `contracts/run-manifest.schema.json` record at every terminal event: completion, intentional stop, failure, abandonment, or scientific acceptance.

- Use an anonymized `case_id` and stable `scientific_protocol_id`.
- Record VASP version, task type, status, acceptance, configuration, observed metrics, evidence labels/checksums, and limitations.
- Do not include POTCAR contents, private absolute paths, hosts, accounts, project names, or unpublished material identifiers.
- Route outputs to `dft-postprocess`; route the terminal manifest and scheduler metrics to `dft-campaign-efficiency`.
- A manifest records evidence; it does not itself prove convergence or physical validity.
