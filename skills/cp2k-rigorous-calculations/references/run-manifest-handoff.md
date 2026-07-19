# CP2K run-manifest handoff

Emit `run_manifest.json` after a technical terminal event: normal completion, intentional stop, failure, or abandonment. It is immutable pre-decision evidence. Encode a deliberate abandonment as `stopped` with an explicit limitation, or as `failed` when the application actually failed; `abandoned` is not a run status.

## Required boundaries

- Use `code: cp2k` and the version printed by the executable.
- Use an opaque anonymized case id and a stable scientific protocol id.
- Use `status=completed` with `scientific_acceptance=not_assessed` or `requires_human_review`; every noncompleted status must remain `not_assessed`.
- Include only privacy-safe configuration fields and metrics.
- Represent input, output, basis, potential, restart, convergence, and task evidence by role, safe label, status, and SHA-256 where permitted.
- Preserve parser, source-version, external-data, restart, task-coverage, convergence, and physical/model limitations.

Never set `status` or `scientific_acceptance` to accepted/rejected and never rewrite the manifest after review. Record a later scientific outcome only through the immutable `calculation-record-envelope → human decision-record → postdecision claim-evidence-map` chain and production bundle validation.

Send the manifest and outputs to `$dft-postprocess` for derived artifacts. Send terminal privacy-safe metrics to `$dft-campaign-efficiency`; accepted/rejected campaign evidence remains blocked until a platform trust resolver authenticates the downstream decision chain. Keep raw calculations, private paths, host/account names, unpublished values, and runtime experience databases outside this repository.
