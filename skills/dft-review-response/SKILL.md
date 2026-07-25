---
name: dft-review-response
description: Build and audit a local point-by-point JSON response draft from supplied reviewer metadata, claim evidence, and proposed changes without editing or submitting a manuscript. Use when review comments require traceable handoffs to active QE, VASP, CP2K, SIESTA, postprocessing, or campaign tooling and unsupported promises must remain blocked.
---

# DFT Review Response

Read [the local official-manual cache route](references/manual-cache-route.md) before promising or citing behavior from an external official document body.

## Start with the repository interface manual

Read [references/repository-interface-manual.md](references/repository-interface-manual.md) first. It defines the implemented CLI, exact candidate artifacts, how new-calculation requests hand off to every active engine, postprocessing/campaign inputs, a runnable synthetic example, and author confirmation points.

## Current status

- **implemented repository interface**: `claim-evidence-map@1.0`, `artifact-manifest@1.0`, `run-manifest@1.0`, and the active calculation/postprocessing/campaign Skills exist.
- **implemented candidate-local interface**: `scripts/review_response_cli.py` writes a fresh candidate plan, audit, and package JSON.
- **design-only**: this Skill is `development`, source-backed at `skills/dft-review-response`, and `routable: false`; `review-comment-set@1.0` and `review-evidence-map@1.0` remain planned interfaces with no active schemas. The development package is neither active interface and does not update a claim map.
- **external not tested**: no manuscript editor, diff engine, journal portal, email, external identity resolver, DFT executable, scheduler, or source service was used.

## Implemented CLI

Run from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-review-response/scripts/review_response_cli.py plan \
  --request skills/dft-review-response/fixtures/valid-review-request.json \
  --claim-map skills/dft-review-response/fixtures/valid-review-claim-map.json \
  --out OUTPUT/response-plan.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-review-response/scripts/review_response_cli.py audit \
  --plan OUTPUT/response-plan.json --out OUTPUT/response-audit.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-review-response/scripts/review_response_cli.py render-package \
  --plan OUTPUT/response-plan.json --audit OUTPUT/response-audit.json \
  --out OUTPUT/response-package.json
```

The commands write candidate-local plan/audit/package JSON and refuse overwrite. Outputs retain `manuscript_modified=false`, `external_message_sent=false`, and `submission_ready=false`.

These commands execute one local no-overwrite JSON write on success; they are not manuscript-editing, send, or submission dry runs. Require `tool_invocation_mode=execute-local-candidate-write`, `local_write_performed=true`, and `external_execution_performed=false`. Build the final structured response as `agent-action-envelope@1.0` and validate it with `tools/validate_agent_answer.py`.

Exit codes are `0` candidate-local gate passed, `2` invalid/privacy-unsafe input, `3` evidence/claim/change/authority blocked, and `4` bounded tool failure. Stop on nonzero. Exit `0` does not prove a manuscript change or submission readiness.

## Manual point-by-point workflow

1. Bind each pseudonymous comment to exactly one response and one proposed change or explicit no-change reason.
2. Bind scientific assertions to present hashed evidence and a bounded claim in an exact `claim-evidence-map@1.0`.
3. If existing evidence is sufficient, run `plan → audit → render-package`; preserve adverse or unresolved findings.
4. If a comment needs a new calculation, an author must decide the scientific objective, observable, tolerance, engine, cost, and response commitment. The candidate cannot promise or authorize the work.
5. Check the selected active Skill route, then manually invoke QE, VASP, CP2K, or SIESTA using the commands in the repository interface manual.
6. After a terminal run, create `run-manifest@1.0`; use `$dft-postprocess` for figures/data and `$dft-campaign-efficiency` for relevant privacy-safe cost evidence.
7. A separate production process must create/authenticate any post-decision claim map, exact manuscript diff, review evidence map, and release decision.
8. Human authors confirm scientific correctness, wording, scope, manuscript edits, and submission. The candidate never sends anything.

## Failure and authority rules

- Polite prose, a successful calculation process, or a visually plausible figure cannot substitute for hashed evidence and scientific gates.
- Do not state that a change is implemented unless an exact manuscript-diff artifact proves it; this candidate accepts only proposed/not-applicable changes.
- Do not merge comments, omit subpoints, fabricate reviewer/editor identity, or hide rejected/deferred work.
- Calculation completion, scientific support, author acceptance, manuscript modification, and submission authorization remain separate.
- Never expose reviewer identities, credentials, private paths, restricted potentials, source text, or unpublished results.

## Additional references

- Use [references/point-by-point-playbook.md](references/point-by-point-playbook.md) to classify comments, select evidence routes, scope new work, draft responses, and verify claimed changes.
- Use [references/linkage-and-role-boundaries.md](references/linkage-and-role-boundaries.md) for one-to-one linkage and author/tool roles.
- Use [references/fail-closed-contract.md](references/fail-closed-contract.md), [references/weak-model-decision-table.json](references/weak-model-decision-table.json), and [references/finding-catalog.json](references/finding-catalog.json) for local gates.
- Use [references/maturity-matrix.json](references/maturity-matrix.json) before any activation discussion.
- Use [references/source-pack-seed.json](references/source-pack-seed.json) and [references/source-pack-scope-catalog.json](references/source-pack-scope-catalog.json) for the blocked metadata-only repository boundary; it never replaces input-specific source or manuscript authorities and can be refreshed or checked with `scripts/extract_official_source_scope.py`.

The development/non-routable candidate's maximum claim is `no_positive_claim`.
