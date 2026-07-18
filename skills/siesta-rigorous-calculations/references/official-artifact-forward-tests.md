# Official artifact forward-tests

`official-artifact-fixtures.json` identifies four standard-output files stored in the official SIESTA repository at tag 5.4.2 / commit `e486d12067b96ff688179f0496d0ec21b6fae0ab`. The skill stores only relative identities, hashes and expected terminal parser values; it does not copy full outputs or pseudopotentials.

Run against an authorized exact official checkout:

```bash
python3 scripts/forward_test_official_artifacts.py \
  --source-tree /authorized/siesta-5.4.2-checkout --pretty
```

The forward-test verifies checkout commit, artifact hashes, unique run boundaries, embedded version grammar, failure-marker precedence, relaxed markers, final total energy and wall-time extraction.

Important maturity boundary: the official tag contains reference outputs whose embedded executable version is `5.0.0-alpha-123-gfb8fd7d02`, not 5.4.2. Therefore this is real official-artifact validation of stable parser grammar and negative-marker precedence only. It is not a 5.4.2 executable forward-test, numerical regression benchmark, or scientific validation.

Upgrade the runtime maturity claim only after testing outputs produced by an exact 5.4.2 executable with legally usable, provenance-complete inputs and pseudopotentials. Keep those runtime artifacts outside the skill unless redistribution and privacy are explicitly safe; a hash-only fixture manifest is preferred.
