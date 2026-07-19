# Synthetic invocation examples

Run from the repository root. The fixtures are synthetic metadata. They demonstrate point-by-point lineage only and are not a real review or scientific result.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B skills/dft-review-response/scripts/review_response_cli.py plan --request skills/dft-review-response/fixtures/valid-review-request.json --claim-map skills/dft-review-response/fixtures/valid-review-claim-map.json --out OUTPUT/response-plan.json
PYTHONDONTWRITEBYTECODE=1 python3 -B skills/dft-review-response/scripts/review_response_cli.py audit --plan OUTPUT/response-plan.json --out OUTPUT/response-audit.json
PYTHONDONTWRITEBYTECODE=1 python3 -B skills/dft-review-response/scripts/review_response_cli.py render-package --plan OUTPUT/response-plan.json --audit OUTPUT/response-audit.json --out OUTPUT/response-package.json
```

Expected candidate-local exit codes are `0`, `0`, and `0`; each summary records `local_write_performed=true` and `external_execution_performed=false`, and all outputs still state no manuscript edit, no external message, and no submission readiness.
