# SIESTA run-manifest and parent handoff

The shared schema and generator support `code=siesta`. Emit a terminal manifest at completion, intentional stop, failure, abandonment, or scientific acceptance:

```bash
python3 ../../tools/create_run_manifest.py \
  --code siesta --code-version <VERSION> --task-type <TASK> \
  --case-id <ANONYMIZED_ID> --protocol-id <PROTOCOL_ID> \
  --status <STATUS> --scientific-acceptance <ACCEPTANCE> \
  --out run_manifest.json
```

The generator creates an empty `evidence` list. Add evidence only through a schema-valid, authorized workflow; do not manually invent hashes or status. A parent consumed by the SIESTA auditor must match the exact shared schema, code/version, case id, and scientific protocol.

For downstream scientific parents, use `status=accepted` and `scientific_acceptance=accepted`, with at least one hashed `present` role permitted by `task-evidence-profiles.json`. For a restart-only parent, a completed parent may remain scientifically unassessed, but it still needs a hashed checkpoint role such as `density_matrix`, `restart_checkpoint`, `structure_checkpoint`, `velocity_checkpoint`, or `siesta_nc`.

Record unavailable metrics as null or omit optional metric properties; never fabricate them. Preserve technical execution, numerical convergence, task validity, physical validity, and scientific acceptance separately in limitations until the shared schema provides dedicated fields.

Keep real paths, hosts/accounts, raw output, unpublished values, and pseudopotential contents outside the manifest. Route output artifacts to `$dft-postprocess`; route privacy-safe terminal metrics and lessons to `$dft-campaign-efficiency`.
