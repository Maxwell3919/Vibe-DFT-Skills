# Repository interface manual

This is the operational entry point for the development `dft-project-orchestrator` Skill. Commands assume the current directory is the root of the `Vibe-DFT-Skills` repository.

## 1. Interface status and authority

| Surface | Status label | Actual repository entry or artifact | What it establishes |
|---|---|---|---|
| Candidate audit | **implemented candidate-local interface** | `skills/dft-project-orchestrator/scripts/orchestrator_cli.py` | Local JSON audit/next-action/authorization comparison only |
| Shared artifacts | **implemented repository interface** | `contracts/{structure-manifest,run-manifest,artifact-manifest,workflow-plan,decision-record,execution-request}.schema.json` | Strict active artifact shapes |
| Route selection | **implemented repository interface** | `tools/operation_routes.py route <skill-id>` | Current routability after registry validation |
| Candidate-to-engine dispatch | **design-only** | no tool, adapter, or registered sequence | A human must invoke the selected active Skill |
| DFT and scheduler execution | **external not tested** | external executables/site scheduler | No execution evidence was collected for this candidate |

`registry/skill-registry.yaml` and `registry/operation-routes.yaml` keep this Skill in development at `skills/dft-project-orchestrator`, with `routable: false`. The active workflow/request/decision schemas do not make this development Skill an active producer.

## 2. Candidate CLI: input and output

All three subcommands are read-only. Shell redirection may save stdout, but the candidate itself writes no file.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-project-orchestrator/scripts/orchestrator_cli.py \
  audit-plan --plan WORKFLOW_PLAN.json > AUDIT_REPORT.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-project-orchestrator/scripts/orchestrator_cli.py \
  next-action --plan WORKFLOW_PLAN.json > NEXT_ACTION.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-project-orchestrator/scripts/orchestrator_cli.py \
  authorize-check --request EXECUTION_REQUEST.json \
  --decision DECISION_RECORD.json --at-utc 2026-07-19T00:00:00Z \
  > AUTHORIZATION_AUDIT.json
```

Inputs are bounded strict UTF-8 JSON objects. Outputs have `contract_name: candidate-orchestrator-report`; they are unsigned candidate reports, not `workflow-plan@1.0`, `decision-record@1.0`, or `execution-request@1.0`.

## 3. Runnable local synthetic example

This example uses only repository fixtures and a temporary directory. It performs no calculation or network access.

```bash
tmp="$(mktemp -d "${TMPDIR:-/tmp}/dft-orchestrator.XXXXXX")"

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-project-orchestrator/scripts/orchestrator_cli.py \
  audit-plan \
  --plan skills/dft-project-orchestrator/fixtures/ready-plan.json \
  > "$tmp/audit.json"

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-project-orchestrator/scripts/orchestrator_cli.py \
  next-action \
  --plan skills/dft-project-orchestrator/fixtures/ready-plan.json \
  > "$tmp/next-action.json"

PYTHONDONTWRITEBYTECODE=1 python3 -B -c \
  'import json,sys; d=json.load(open(sys.argv[1])); print(d["status"], d["minimum_next_action"], d["claim_ceiling"])' \
  "$tmp/audit.json"

PYTHONDONTWRITEBYTECODE=1 python3 -B -c \
  'import json,sys; d=json.load(open(sys.argv[1])); print(d["status"], d["minimum_next_action"], d["execution_authorized"])' \
  "$tmp/next-action.json"
```

Expected values are `pass`, `prepare-immutable-execution-request-for-synthetic-step-001`, `no_positive_claim`, and `execution_authorized=false`. The example leaves the temporary files for inspection.

The negative fixture is also runnable and must return exit `2` because it contains a dependency cycle:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-project-orchestrator/scripts/orchestrator_cli.py \
  audit-plan \
  --plan skills/dft-project-orchestrator/fixtures/cycle-plan.json
```

## 4. Route and contract gates before a handoff

Run the route check for the exact terminal Skill, not for a natural-language alias:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/operation_routes.py route qe-rigorous-calculations
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/operation_routes.py route vasp-rigorous-calculations
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/operation_routes.py route cp2k-rigorous-calculations
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/operation_routes.py route siesta-rigorous-calculations
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/operation_routes.py route dft-postprocess
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/operation_routes.py route dft-campaign-efficiency
```

Any nonzero exit, `decision: blocked`, or `route: null` stops the handoff. Do not rely only on the lifecycle text in YAML.

Validate an active artifact before use:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/validate_contract.py workflow-plan WORKFLOW_PLAN.json
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/validate_contract.py execution-request EXECUTION_REQUEST.json
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/validate_contract.py decision-record DECISION_RECORD.json
```

If an immutable bundle manifest exists, validate the exact bundle rather than loose files:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/validate_bundle.py BUNDLE_MANIFEST.json --report BUNDLE_REPORT.json
```

## 5. Exact manual engine handoff

The orchestrator candidate never invokes these commands. The operator selects exactly one engine after human confirmation of objective, task, observable, tolerance, software version, structure, method, and provenance.

### Quantum ESPRESSO

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/qe-rigorous-calculations/scripts/qe_guard.py audit \
  --input CASE/scf.in --output CASE/scf.out --run-dir CASE \
  --pseudo-dir CASE/pseudo --pseudo-manifest CASE/pseudopotential-manifest.json \
  --expected-version VERSION --plan CASE/qe-plan.json \
  --out CASE/qe-run-audit.json
```

**implemented repository interface**: active Skill script and its deterministic audit. **External not tested here**: `pw.x`, MPI/launcher behavior, and the supplied scientific case.

### VASP

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/vasp-rigorous-calculations/scripts/audit_vasp_case.py CASE \
  --mode run --task-type TASK --pretty > CASE/vasp-run-audit.json
```

**implemented repository interface**: active Skill script. **External not tested here**: VASP execution, licensed POTCAR access, and the supplied case.

### CP2K

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/cp2k-rigorous-calculations/scripts/audit_cp2k_case.py CASE/input.inp \
  --mode run --task-type TASK --output CASE/main.out \
  --data-file BASIS_FILE --data-file POTENTIAL_FILE --pretty \
  > CASE/cp2k-run-audit.json
```

**implemented repository interface**: active Skill script. **External not tested here**: CP2K execution and actual basis/potential data.

### SIESTA

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/siesta-rigorous-calculations/scripts/audit_siesta_case.py CASE/input.fdf \
  --mode run --task-type TASK --periodicity PERIODICITY \
  --plan CASE/scientific-plan.json --expected-version VERSION \
  --output CASE/run.out \
  --pseudopotential-manifest CASE/pseudopotential-manifest.json \
  --out CASE/siesta-run-audit.json
```

**implemented repository interface**: active Skill script. **External not tested here**: SIESTA execution and the supplied case.

An input or run audit can only establish its documented gate ceiling. It does not grant execution or scientific acceptance.

## 6. Terminal run, postprocess, and campaign handoffs

At a real terminal event, the selected active calculation Skill creates the active `run-manifest@1.0` through the repository tool:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/create_run_manifest.py \
  --code ENGINE --code-version VERSION --task-type TASK \
  --case-id ANONYMIZED_CASE_ID --protocol-id PROTOCOL_ID \
  --status STATUS --scientific-acceptance not_assessed \
  --out CASE/run_manifest.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  tools/validate_contract.py run-manifest CASE/run_manifest.json
```

`ENGINE` must be exactly one of `qe`, `vasp`, `cp2k`, or `siesta`. Use a real terminal `STATUS` (`completed`, `stopped`, or `failed`) only when the corresponding event evidence exists; never fabricate it for a production record.

Manual postprocess entry:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-postprocess/scripts/dftpost_cli.py inventory CASE \
  --out CASE/postprocess-inventory.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-postprocess/scripts/dftpost_cli.py capabilities \
  --out CASE/postprocess-capabilities.json
```

Choose the observable-specific postprocess subcommand only after reading that active Skill's maturity registry. Do not assume the QE/VASP `extract-summary` route covers CP2K or SIESTA.

Manual campaign entry:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-campaign-efficiency/scripts/dft_efficiency_cli.py from-run \
  CASE/run_manifest.json --system-class ANONYMIZED_CLASS --atom-count N \
  --configuration-id CONFIGURATION_ID --out CASE/campaign_record.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  tools/validate_contract.py campaign-record CASE/campaign_record.json
```

The campaign record is privacy-safe efficiency evidence, not a scientific conclusion.

## 7. Human confirmation points

A human must confirm before:

1. selecting or changing the scientific objective, observable, tolerance, model, or engine;
2. turning a plan step into an immutable execution request;
3. authorizing any local, remote, or scheduler side effect;
4. retrying, cancelling, or abandoning a run;
5. accepting/rejecting a scientific claim or releasing a report.

No candidate report can stand in for these decisions.

## 8. Plan, lease, event, evidence, and answer protocol

Keep each record immutable and link forward by exact raw-byte SHA-256:

```text
workflow-plan -> execution-request -> decision-record -> execution-lease
       |                  |                    |              |
       +------------------+--------------------+------> workflow-event(s)
                                                       |
                                               execution-record/run-manifest
                                                       |
                                            evidence-record/claim-evidence-map
                                                       |
                                                agent-action-envelope
```

The arrows mean content-addressed lineage, not authority inheritance. A plan does not authorize its request; a decision does not issue its lease; a lease does not prove execution; an event does not prove application completion; a run manifest does not prove convergence; and an answer envelope does not authenticate any upstream record.

| Contract | Required use | Candidate behavior |
|---|---|---|
| `workflow-plan@1.0` | DAG, route lifecycle, input/output contracts, side-effect policy, gates | Audited by `audit-plan` and `next-action` only |
| `execution-request@1.0` | Exact plan step, argv, resources, input hashes, outputs, timeout, retry and side effects | Checked with a separate decision by `authorize-check` |
| `decision-record@1.0` | Human outcome for the exact request or exact scientific subject | Consumed, never created or authenticated |
| `execution-lease@1.0` | Expiring single-use non-broadening grant | Requested as the next action after authorization; never issued here |
| `workflow-event@1.0` | Append-only ordered observation with exact plan/step refs | Never emitted here; event conflicts block continuation |
| `evidence-record@1.0` and `claim-evidence-map@1.0` | Separate observation from bounded claim and human decision lineage | Required before review; conversation prose is not evidence |
| `agent-action-envelope@1.0` | Machine-checkable final agent answer | Created outside the candidate CLI and validated separately |

Build the final answer envelope from exact output bytes, preserve the route decision and all blockers, and name only one smallest next action. Validate it before presenting a trust-bearing answer:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  tools/validate_agent_answer.py ANSWER_ENVELOPE.json --pretty
```

Exit `0` means internally consistent with no trust-bearing positive claim. Exit `3` means external bundle verification is required. Exit `2` blocks. The candidate report is supporting tool output, not the answer contract itself.

## 9. Dry-run, execute, and acceptable workflow

All candidate commands are inspection-only dry runs: they write no files and perform no downstream tool or scheduler action. Add no `execute` interpretation to an exit `0`. An execution path requires, in order, an active exact route, a validated immutable request, an exact human authorization decision, a fresh matching lease, a separately registered executor, and later append-only events/records.

A synthetic orchestration workflow is acceptable only when:

1. `tools/operation_routes.py route` is checked for every selected terminal Skill and every selected route is active;
2. `audit-plan` exits `0`, the DAG is acyclic, the first ready step has satisfied dependencies/gates, and the next action is exactly one bounded action;
3. any side-effecting step declares human-decision and lease requirements before a request is produced;
4. `authorize-check` binds exact request and decision bytes and still returns only `request-bounded-single-use-lease` as the next action;
5. later scheduler, process, application, numerical, and scientific states are recorded separately through external records;
6. the final answer envelope validates at the actual evidence ceiling.

If the repository registry is invalid or drifted, route resolution itself is blocked; do not fall back to lifecycle prose or a remembered route.
