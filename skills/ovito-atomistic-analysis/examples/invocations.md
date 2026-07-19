# Candidate invocation examples

Run from this candidate directory. These commands do not activate the candidate.

```bash
python3 scripts/ovito_analysis.py inventory fixtures/two-frame.extxyz --out inventory.json
python3 scripts/ovito_analysis.py plan --inventory inventory.json \
  --pipeline fixtures/metadata-pipeline.json --out plan.json
python3 scripts/ovito_analysis.py plan --inventory inventory.json --pipeline fixtures/pro-render-pipeline.json --require-execution-ready
python3 scripts/ovito_analysis.py probe
```

Only run the following after the user explicitly authorizes external execution and a matching
Basic module is available:

```bash
python3 scripts/ovito_analysis.py execute --source fixtures/two-frame.extxyz \
  --inventory inventory.json --pipeline fixtures/metadata-pipeline.json \
  --authorize-execution --authorization-scope SCOPE_SHA256_FROM_PLAN \
  --out execution-result.json
```

Read `authorization_scope_sha256` from `plan.json` and substitute it exactly; do not reuse a scope
after changing any bound source, spec, provider, frame, or operation. Output names must not exist
or alias evidence. Every report remains lifecycle-capped at `no_positive_claim` while in development.
