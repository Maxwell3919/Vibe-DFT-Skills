---
name: dft-reporting
description: Build and audit a local JSON report draft from supplied claim, artifact, and campaign records without running calculations or publishing. Use when an evidence package from QE, VASP, CP2K, SIESTA, postprocessing, or campaign analysis must be assembled manually and its active versus planned repository interfaces kept explicit.
---

# DFT Reporting

Read [the local official-manual cache route](references/manual-cache-route.md) before reporting facts drawn from an external official document body.

## Start with the repository interface manual

Read [references/repository-interface-manual.md](references/repository-interface-manual.md) first. It gives the exact CLI, candidate output artifacts, active upstream entry points for all four engines plus postprocessing and campaign records, a runnable synthetic chain, and release confirmation points.

## Current status

- **implemented repository interface**: `claim-evidence-map@1.0`, `artifact-manifest@1.0`, `campaign-record@1.0`, and the active calculation/postprocessing/campaign Skills have repository contracts and scripts.
- **implemented candidate-local interface**: `scripts/reporting_cli.py` writes a fresh candidate plan, audit, and package JSON.
- **design-only**: `dft-reporting` is `development`, source-backed at `skills/dft-reporting`, and `routable: false`; `review-evidence-map@1.0` and `scientific-report@1.0` remain planned interfaces with no active schema. Development JSON is not either active contract.
- **external not tested**: no manuscript renderer, journal system, email, cloud document, publication endpoint, DFT executable, or external source resolver was used.

## Implemented CLI

Run from the repository root and write only to a new output directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-reporting/scripts/reporting_cli.py plan \
  --request skills/dft-reporting/fixtures/valid-report-request.json \
  --claim-map skills/dft-reporting/fixtures/valid-claim-map.json \
  --out OUTPUT/report-plan.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-reporting/scripts/reporting_cli.py audit \
  --plan OUTPUT/report-plan.json --out OUTPUT/report-audit.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-reporting/scripts/reporting_cli.py render-package \
  --plan OUTPUT/report-plan.json --audit OUTPUT/report-audit.json \
  --out OUTPUT/report-package.json
```

The commands write, respectively, `scientific-report-candidate-plan`, `dft-report-candidate-audit`, and `scientific-report-candidate-package` JSON objects. They refuse overwrite. Every package keeps `publication_ready=false` and `external_message_sent=false`.

These are executed local no-overwrite writes, not dry runs of file creation. Require `tool_invocation_mode=execute-local-candidate-write`, `local_write_performed=true`, and `external_execution_performed=false` after a successful command. Build any final structured response as `agent-action-envelope@1.0` and validate it with `tools/validate_agent_answer.py`.

Exit codes are `0` candidate-local gate passed, `2` invalid/privacy-unsafe input, `3` evidence or authority blocked, and `4` bounded tool failure. Stop on any nonzero exit. Exit `0` is not scientific acceptance or release approval.

## Manual evidence workflow

1. Select a bounded claim from an exact `claim-evidence-map@1.0`; do not draft from conversation memory.
2. For every calculation claim, retain the active engine's technical audit and terminal `run-manifest@1.0`.
3. Use `$dft-postprocess` to create the data/figure artifacts and `artifact-manifest@1.0`; use `$dft-campaign-efficiency` only when cost/workflow evidence is relevant.
4. Validate active contracts with `tools/validate_contract.py` and any immutable bundle with `tools/validate_bundle.py`.
5. Run the candidate `plan → audit → render-package` chain. Do not hand-edit generated JSON to remove a blocker.
6. A human author must confirm scientific meaning, adverse findings, citation accuracy, audience, wording, and release scope.
7. Conversion to a manuscript or `scientific-report@1.0`, publication, submission, or sending is outside the implemented interface.

## Failure and authority rules

- A filename, prose assertion, figure appearance, successful render, or hash alone is not scientific evidence.
- Calculation completion, numerical support, physical validity, human scientific acceptance, and publication authorization are separate gates.
- Preserve unsupported, rejected, or unresolved claims and limitations; do not polish around them.
- Do not infer citation authority or decision authenticity. External resolvers and human confirmation remain required.
- Never expose credentials, private paths, reviewer identities, restricted potentials, or unpublished source text.

## Additional references

- Use [references/report-content-playbook.md](references/report-content-playbook.md) to assemble claim-first methods, results, validation, figures/tables, negative results, and reproducibility content.
- Use [references/workflow-and-roles.md](references/workflow-and-roles.md) for author/tool/reviewer role separation.
- Use [references/fail-closed-contract.md](references/fail-closed-contract.md) and [references/weak-model-decision-table.json](references/weak-model-decision-table.json) for local gate order.
- Use [references/finding-catalog.json](references/finding-catalog.json) for findings and [references/maturity-matrix.json](references/maturity-matrix.json) for activation gaps.
- Use [references/source-pack-seed.json](references/source-pack-seed.json) and [references/source-pack-scope-catalog.json](references/source-pack-scope-catalog.json) for the blocked metadata-only repository-interface boundary; refresh or check them with `scripts/extract_official_source_scope.py`.

The development/non-routable candidate's own maximum claim is `no_positive_claim`.
