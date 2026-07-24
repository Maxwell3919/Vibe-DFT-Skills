---
name: literature-to-dft-plan
description: Convert supplied, content-addressed literature metadata and bounded facts into an offline candidate DFT plan while separating source assertions, numerical facts, inferences, and project choices. Use when a human must hand the plan to active QE, VASP, CP2K, or SIESTA tooling without implying that sources were fetched, a route was activated, or a calculation ran.
---

# Literature to DFT Plan

## Start with the repository interface manual

Read [references/repository-interface-manual.md](references/repository-interface-manual.md) first. It records the exact offline CLI, request/output artifacts, active calculation entry points, postprocess/campaign handoffs, runnable synthetic chain, and human decisions that cannot be automated.

## Current status

- **implemented repository interface**: `official-source-record@1.0`, `evidence-record@1.0`, `structure-manifest@1.0`, `run-manifest@1.0`, and the active calculation/postprocessing/campaign Skills exist in the repository.
- **implemented candidate-local interface**: `scripts/literature_plan_cli.py` writes a fresh candidate plan, audit, and package JSON from supplied local records.
- **design-only**: this Skill is `development`, source-backed at `skills/literature-to-dft-plan`, and `routable: false`; `literature-evidence-plan@1.0` remains a planned interface with no active schema. The package is not an activated calculation input.
- **external not tested**: no paper database, publisher, DOI resolver, web page, official manual, network service, DFT executable, or scheduler was contacted.

## Implemented CLI

Run from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/literature-to-dft-plan/scripts/literature_plan_cli.py plan \
  --request skills/literature-to-dft-plan/fixtures/valid-literature-request.json \
  --out OUTPUT/literature-plan.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/literature-to-dft-plan/scripts/literature_plan_cli.py audit \
  --plan OUTPUT/literature-plan.json --out OUTPUT/literature-audit.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/literature-to-dft-plan/scripts/literature_plan_cli.py render-package \
  --plan OUTPUT/literature-plan.json --audit OUTPUT/literature-audit.json \
  --out OUTPUT/literature-package.json
```

The outputs are candidate-local plan/audit/package objects. They refuse overwrite and keep `network_access_performed=false`, `calculation_authorized=false`, and `execution_started=false`.

These commands execute one local no-overwrite JSON write on success; they are not paper-retrieval or calculation dry runs. Require `tool_invocation_mode=execute-local-candidate-write`, `local_write_performed=true`, and `external_execution_performed=false`. Build the final structured response as `agent-action-envelope@1.0` and validate it with `tools/validate_agent_answer.py`.

Exit codes are `0` candidate-local check passed, `2` malformed/privacy-unsafe input, `3` source/route/evidence/authority blocked, and `4` bounded tool failure. Stop on nonzero. Exit `0` does not authenticate a source or approve a calculation.

## Manual source-to-calculation workflow

1. A human or external retrieval process supplies source metadata, exact content hashes, bounded locators, license state, and redistribution limits. A DOI, title, abstract memory, or URL alone is not extracted evidence.
2. Classify each item as source assertion, quoted numerical fact, inference, project choice, or new-claim proposal. Never merge these roles.
3. Run `plan → audit → render-package`; retain blockers and limitations.
4. A human chooses the scientific objective, observable, tolerance, model assumptions, code, software version, and validation burden.
5. Check the chosen active Skill route. A nonzero, development, planned, blocked, or null route stops handoff.
6. Manually translate only the chosen calculation step into the selected active `$qe-rigorous-calculations`, `$vasp-rigorous-calculations`, `$cp2k-rigorous-calculations`, or `$siesta-rigorous-calculations` workflow. The candidate performs no conversion or invocation.
7. After an authorized terminal run, create `run-manifest@1.0`; send outputs to `$dft-postprocess` and privacy-safe cost records to `$dft-campaign-efficiency`.

## Failure and authority rules

- A source inventory proves only what was supplied, not truth, authority, completeness, or license.
- Version-sensitive facts require matching source/software versions; do not project behavior across versions.
- Project choices remain assumptions even when a user approves them.
- A proposed inference or claim remains a question until new evidence and human review support it.
- Never reproduce restricted source text, credentials, private paths, unpublished results, or licensed potential content.

## Additional references

- Use [references/evidence-extraction-playbook.md](references/evidence-extraction-playbook.md) for source extraction, method comparability, conflicting literature, parameter transfer, and calculation translation.
- Use [references/classification-and-lineage.md](references/classification-and-lineage.md) for the five semantic classes.
- Use [references/source-and-license-policy.md](references/source-and-license-policy.md) for source boundaries.
- Use [references/fail-closed-contract.md](references/fail-closed-contract.md), [references/weak-model-decision-table.json](references/weak-model-decision-table.json), and [references/finding-catalog.json](references/finding-catalog.json) for deterministic local gates.
- Use [references/maturity-matrix.json](references/maturity-matrix.json) before any activation discussion.
- Use [references/source-pack-seed.json](references/source-pack-seed.json) and [references/source-pack-scope-catalog.json](references/source-pack-scope-catalog.json) for the blocked metadata-only repository boundary; it deliberately excludes a finite universal literature corpus and can be refreshed or checked with `scripts/extract_official_source_scope.py`.

The development/non-routable candidate's maximum claim is `no_positive_claim`.
