# SIESTA run-manifest and parent handoff

The shared schema and generator support `code=siesta`. Emit an immutable pre-decision manifest at a technical completion, intentional stop, failure, or abandonment. Encode deliberate abandonment as `stopped` with an explicit limitation, or as `failed` when the application actually failed; never invent an `abandoned` status:

```bash
python3 ../../tools/create_run_manifest.py \
  --code siesta --code-version <VERSION> --task-type <TASK> \
  --case-id <ANONYMIZED_ID> --protocol-id <PROTOCOL_ID> \
  --status <STATUS> --scientific-acceptance <ACCEPTANCE> \
  --out run_manifest.json
```

The generator defaults to an empty `evidence` list when `--evidence` is omitted. Supply an authorized, strictly parsed JSON evidence array with `--evidence`; every `present` item needs its exact lowercase SHA-256, while a `missing` item cannot carry a hash. Do not manually invent hashes or status. A parent consumed by the SIESTA auditor must match the exact shared schema, code/version, case id, and scientific protocol.

Use `status=completed` with `scientific_acceptance=not_assessed` or `requires_human_review`. Every noncompleted status must remain `not_assessed`. Never write `accepted` or `rejected` into the run manifest or rewrite it after a decision.

For a restart-only parent, require `status=completed` and a hashed checkpoint role such as `density_matrix`, `restart_checkpoint`, `structure_checkpoint`, `velocity_checkpoint`, or `siesta_nc`; scientific acceptance is not required merely to reuse a verified checkpoint. For a downstream scientific parent, separately require a production-validated immutable chain: run manifest → calculation record → human scientific decision → post-decision claim map. The current SIESTA CLI has no externally trusted human-identity resolver, so it returns `PARENT_SCIENTIFIC_DECISION_BUNDLE_REQUIRED` instead of accepting a self-declared manifest.

Record unavailable metrics as null or omit optional metric properties; never fabricate them. Preserve technical execution, numerical convergence, task validity, physical validity, and scientific acceptance separately in limitations until the shared schema provides dedicated fields.

Keep real paths, hosts/accounts, raw output, unpublished values, and pseudopotential contents outside the manifest. Route output artifacts to `$dft-postprocess`; route privacy-safe terminal metrics and lessons to `$dft-campaign-efficiency`.
