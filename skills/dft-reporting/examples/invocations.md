# Synthetic invocation examples

Run all commands from the repository root. The fixtures contain only synthetic metadata and do not establish a scientific result.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B skills/dft-reporting/scripts/reporting_cli.py plan --request skills/dft-reporting/fixtures/valid-report-request.json --claim-map skills/dft-reporting/fixtures/valid-claim-map.json --out OUTPUT/report-plan.json
PYTHONDONTWRITEBYTECODE=1 python3 -B skills/dft-reporting/scripts/reporting_cli.py audit --plan OUTPUT/report-plan.json --out OUTPUT/report-audit.json
PYTHONDONTWRITEBYTECODE=1 python3 -B skills/dft-reporting/scripts/reporting_cli.py render-package --plan OUTPUT/report-plan.json --audit OUTPUT/report-audit.json --out OUTPUT/report-package.json
```

Expected local exit codes are `0`, `0`, and `0`. Each summary records `local_write_performed=true` and `external_execution_performed=false`. Every artifact still states `publication_ready=false`, `external_message_sent=false`, and external trust limitations.
