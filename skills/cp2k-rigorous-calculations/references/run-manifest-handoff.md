# CP2K run-manifest handoff

Emit `run_manifest.json` after a terminal event: normal completion, intentional stop, failure, abandonment, rejection, or scientific acceptance.

## Required boundaries

- Use `code: cp2k` and the version printed by the executable.
- Use an opaque anonymized case id and a stable scientific protocol id.
- Record technical run status separately from `scientific_acceptance`.
- Include only privacy-safe configuration fields and metrics.
- Represent input, output, basis, potential, restart, convergence, and task evidence by role, safe label, status, and SHA-256 where permitted.
- Preserve parser, source-version, external-data, restart, task-coverage, convergence, and physical/model limitations.

Do not set `scientific_acceptance: accepted` from a passing input audit, a technically complete output, or a stable-tail candidate alone.

Send the manifest and outputs to `$dft-postprocess` for derived artifacts. Send terminal privacy-safe metrics and accepted/rejected state to `$dft-campaign-efficiency`. Keep raw calculations, private paths, host/account names, unpublished values, and runtime experience databases outside this repository.
