# Repository interface manual

This manual separates the implemented local dry-run surface from the design-only executor and external Slurm operations. Run repository commands from the `Vibe-DFT-Skills` root.

## 1. What exists

| Surface | Status label | Entry/artifact | Actual behavior |
|---|---|---|---|
| Request/dry-run/status check | **implemented candidate-local interface** | `skills/dft-hpc-execution/scripts/hpc_execution_cli.py` | Reads bounded JSON; emits one candidate report to stdout |
| Shared execution records | **implemented repository interface** | active `execution-request`, `decision-record`, `execution-lease`, `execution-record`, `workflow-event` contracts | Validatable artifact shapes; not an executor |
| Slurm adapter/lease issuer/status collector | **design-only** | none | No registered tool sequence or side-effect implementation |
| Cluster commands and DFT run | **external not tested** | `sbatch`, `squeue`, `sacct`, `scancel`, `scontrol`, DFT executable | Not invoked by this candidate or its tests |

The Skill is in development at `skills/dft-hpc-execution` and has `routable: false`. A dry-run report is `candidate-hpc-report`, not an `execution-record@1.0` or a lease.

## 2. Implemented CLI and artifacts

### Validate a request

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-hpc-execution/scripts/hpc_execution_cli.py \
  validate-request --request EXECUTION_REQUEST.json \
  > REQUEST_AUDIT.json
```

Input: one `execution-request` JSON object. Output: candidate report on stdout. No authorization is created.

### Render Slurm intent

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-hpc-execution/scripts/hpc_execution_cli.py \
  render-dry-run --request EXECUTION_REQUEST.json \
  --decision DECISION_RECORD.json --lease EXECUTION_LEASE.json \
  --scheduler slurm --at-utc 2026-07-19T00:00:00Z \
  > RENDER_REPORT.json
```

Output fields include `rendered_script`, `rendered_script_sha256`, and `proposed_submission_argv`. The report always states `side_effect_performed=false` and `scheduler_job_id=null`. The candidate neither writes the script nor runs `sbatch`.

### Classify supplied observations

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-hpc-execution/scripts/hpc_execution_cli.py \
  classify-status --observation STATUS_OBSERVATION.json \
  > STATUS_CLASSIFICATION.json
```

This normalizes supplied evidence only. Exit `0` means the classification ran; read `states.normalized_execution` for the result.

## 3. Runnable local synthetic example

```bash
tmp="$(mktemp -d "${TMPDIR:-/tmp}/dft-hpc.XXXXXX")"

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-hpc-execution/scripts/hpc_execution_cli.py \
  validate-request \
  --request skills/dft-hpc-execution/fixtures/slurm-request.json \
  > "$tmp/request-audit.json"

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-hpc-execution/scripts/hpc_execution_cli.py \
  render-dry-run \
  --request skills/dft-hpc-execution/fixtures/slurm-request.json \
  --decision skills/dft-hpc-execution/fixtures/slurm-decision.json \
  --lease skills/dft-hpc-execution/fixtures/slurm-lease.json \
  --scheduler slurm --at-utc 2026-07-19T00:00:00Z \
  > "$tmp/render-report.json"

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-hpc-execution/scripts/hpc_execution_cli.py \
  classify-status \
  --observation skills/dft-hpc-execution/fixtures/scheduler-success-app-failure.json \
  > "$tmp/status.json"

PYTHONDONTWRITEBYTECODE=1 python3 -B -c \
  'import json,sys; d=json.load(open(sys.argv[1])); print(d["dry_run"], d["side_effect_performed"], d["scheduler_job_id"], d["rendered_script_sha256"])' \
  "$tmp/render-report.json"

PYTHONDONTWRITEBYTECODE=1 python3 -B -c \
  'import json,sys; d=json.load(open(sys.argv[1])); print(d["states"]["scheduler"], d["states"]["application"], d["states"]["normalized_execution"])' \
  "$tmp/status.json"
```

The render inspection must show `True False None <sha256>`. The supplied observation intentionally separates a successful scheduler state from an application failure; the normalized result must not be success. No command above contacts Slurm.

## 4. Route and contract checks

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/operation_routes.py route dft-hpc-execution
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/validate_contract.py execution-request EXECUTION_REQUEST.json
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/validate_contract.py decision-record DECISION_RECORD.json
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/validate_contract.py execution-lease EXECUTION_LEASE.json
```

The current development/non-routable route must not be treated as executable. Any repository validator failure blocks the manual procedure.

## 5. Engine command binding

An execution request must carry `command_kind=argv`, `shell=false`, and one exact argv. The request is engine-specific; the candidate does not discover or rewrite it.

| Engine Skill | Typical executable binding in a reviewed request | Required pre-run local gate | Status |
|---|---|---|---|
| `$qe-rigorous-calculations` | `pw.x -in scf.in` | `skills/qe-rigorous-calculations/scripts/qe_guard.py audit ...` | **implemented repository interface**; executable **external not tested** |
| `$vasp-rigorous-calculations` | site-approved VASP executable/launcher argv | `skills/vasp-rigorous-calculations/scripts/audit_vasp_case.py CASE --mode input ...` | **implemented repository interface**; licensed executable **external not tested** |
| `$cp2k-rigorous-calculations` | site-approved CP2K executable/launcher argv | `skills/cp2k-rigorous-calculations/scripts/audit_cp2k_case.py CASE/input.inp --mode input ...` | **implemented repository interface**; executable **external not tested** |
| `$siesta-rigorous-calculations` | site-approved SIESTA executable/launcher argv | `skills/siesta-rigorous-calculations/scripts/audit_siesta_case.py CASE/input.fdf --mode input ...` | **implemented repository interface**; executable **external not tested** |

Do not copy the `pw.x` fixture argv to another engine. The human operator must supply the executable path, launcher, modules/container, version, working directory, and site policy. The candidate must reject shell strings and unapproved broadening.

## 6. Slurm handoff

The only operational scheduler procedure documented here is [slurm-operations.md](slurm-operations.md). It provides exact patterns for:

- `sbatch --parsable SCRIPT` submission;
- `squeue` active observation;
- `sacct` accounting/terminal observation;
- `scontrol` detailed inspection;
- `scancel` human-confirmed cancellation.

Every one of those commands is **external not tested** in this candidate task. A human must review the rendered script and site policy and explicitly confirm submission or cancellation. The script materialization and exact hash binding are **design-only** because no repository executor implements them.

## 7. Terminal artifact handoff

After a real terminal application event—not merely a Slurm state—the active calculation workflow creates a canonical run manifest:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/create_run_manifest.py \
  --code ENGINE --code-version VERSION --task-type TASK \
  --case-id ANONYMIZED_CASE_ID --protocol-id PROTOCOL_ID \
  --status STATUS --scientific-acceptance not_assessed \
  --out CASE/run_manifest.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  tools/validate_contract.py run-manifest CASE/run_manifest.json
```

`ENGINE` is `qe`, `vasp`, `cp2k`, or `siesta`. The run output and active Skill audit—not the scheduler alone—determine whether `completed`, `stopped`, or `failed` is supportable.

Postprocessing entry:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-postprocess/scripts/dftpost_cli.py inventory CASE \
  --out CASE/postprocess-inventory.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-postprocess/scripts/dftpost_cli.py capabilities \
  --out CASE/postprocess-capabilities.json
```

Campaign entry:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-campaign-efficiency/scripts/dft_efficiency_cli.py from-run \
  CASE/run_manifest.json --system-class ANONYMIZED_CLASS --atom-count N \
  --configuration-id CONFIGURATION_ID --out CASE/campaign_record.json
```

These are active repository interfaces. Their scientific and privacy gates still apply; no positive conclusion follows from record creation.

## 8. Human confirmation points

Explicit human confirmation is required before:

1. accepting a site environment/account/partition/QoS/launcher/storage profile;
2. materializing the rendered script as the exact reviewed bytes;
3. invoking `sbatch`;
4. retrying an uncertain or failed attempt;
5. invoking `scancel` or another scheduler-control command;
6. calling an application technically complete, scientifically adequate, accepted, or releasable.

## 9. Request, lease, record, event, and answer protocol

Use exact forward lineage:

```text
workflow-plan -> execution-request -> human decision -> execution-lease
                                      (exact hashes)          |
                                                               v
                                      external executor -> execution-record
                                                               |
                                                      workflow-event(s)
                                                               |
                                                   run-manifest/evidence
                                                               |
                                                   agent-action-envelope
```

| Contract | Required rule | Candidate behavior |
|---|---|---|
| `execution-request@1.0` | Immutable argv/resources/inputs/outputs/side effects for one plan step | Validated locally |
| `decision-record@1.0` | Human approval of the exact request hash, scope, side effects, and validity interval | Consumed, never created/authenticated |
| `execution-lease@1.0` | Active, unexpired, single-use, exact request+decision binding, non-broadening grant | Validated for rendering; never consumed by a dry run |
| `execution-record@1.0` | What an external executor actually attempted and observed | Not emitted by this candidate |
| `workflow-event@1.0` | Append-only plan/step state observation with monotonic sequence | Not emitted by this candidate |
| `run-manifest@1.0` | Terminal application handoff after engine-specific audit | Not inferred from scheduler status |
| `agent-action-envelope@1.0` | Structured agent answer with route, tool run, evidence, gates, authorization, and next action | Built and validated outside this CLI |

Unknown submission outcome, repeated lease use, duplicate/conflicting events, request drift, or a missing application completion record blocks retry and downstream success claims.

Validate the final answer envelope with:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  tools/validate_agent_answer.py ANSWER_ENVELOPE.json --pretty
```

Exit `0` means internal consistency only at no trust-bearing positive claim. Exit `3` requires external content-hash and record-semantic bundle verification. Exit `2` blocks.

## 10. Dry-run versus execute acceptance

`validate-request`, `render-dry-run`, and `classify-status` execute local Python inspection only. They perform no scheduler or remote side effect. `render-dry-run` must retain all of these values:

```text
dry_run=true
side_effect_performed=false
scheduler_job_id=null
lease_consumed=false
workflow_event_emitted=false
```

There is no candidate `execute` subcommand. A real external executor may act only after route activation and exact validation of request, decision, lease, environment/site policy, and reviewed script hash. It must atomically consume the lease, record the attempt, preserve uncertain outcome, and emit separate state observations; these behaviors are design requirements, not implemented here.

Accept the synthetic HPC workflow only when the request/decision/lease chain validates, the Slurm renderer produces deterministic exact bytes and argv without consuming the lease, the supplied status fixture preserves scheduler/process/application separation, and the answer envelope reports the candidate route as blocked rather than executable.
