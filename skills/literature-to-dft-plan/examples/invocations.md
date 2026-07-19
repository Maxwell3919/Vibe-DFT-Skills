# Synthetic invocation examples

Run from the repository root. The fixture contains only synthetic metadata. It demonstrates classification and lineage, not a literature fact or DFT conclusion.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B skills/literature-to-dft-plan/scripts/literature_plan_cli.py plan --request skills/literature-to-dft-plan/fixtures/valid-literature-request.json --out OUTPUT/literature-plan.json
PYTHONDONTWRITEBYTECODE=1 python3 -B skills/literature-to-dft-plan/scripts/literature_plan_cli.py audit --plan OUTPUT/literature-plan.json --out OUTPUT/literature-audit.json
PYTHONDONTWRITEBYTECODE=1 python3 -B skills/literature-to-dft-plan/scripts/literature_plan_cli.py render-package --plan OUTPUT/literature-plan.json --audit OUTPUT/literature-audit.json --out OUTPUT/literature-package.json
```

Expected candidate-local exit codes are `0`, `0`, and `0`. Each summary records `local_write_performed=true` and `external_execution_performed=false`. The package still has `claim_ceiling=no_positive_claim`, no network access, no execution authorization, and no external message.
