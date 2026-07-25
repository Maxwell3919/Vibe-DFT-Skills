---
name: dft-hpc-execution
description: Validate supplied DFT execution requests and render a Slurm batch script as a local dry run, then classify supplied scheduler, process, and application observations without contacting a cluster. Use when a human operator needs an exact manual Slurm submission, observation, cancellation, and downstream artifact procedure with authorization boundaries kept explicit.
---

# DFT HPC Execution

Read [the local official-manual cache route](references/manual-cache-route.md) before relying on external scheduler or standard documentation bodies.

## Start with the manuals

Read [references/repository-interface-manual.md](references/repository-interface-manual.md) for the candidate CLI and DFT artifact handoffs. Read [references/slurm-operations.md](references/slurm-operations.md) before any Slurm operation. The latter uses only official SchedMD documentation and marks all cluster commands **external not tested**.

## Current status

- **implemented repository interface**: `execution-request@1.0`, `decision-record@1.0`, `execution-lease@1.0`, `execution-record@1.0`, and `workflow-event@1.0` have active repository contracts.
- **implemented candidate-local interface**: `scripts/hpc_execution_cli.py` validates supplied records, renders text plus a proposed argv, and classifies supplied observations. It never invokes the argv.
- **design-only**: this Skill is `development`, source-backed at `skills/dft-hpc-execution`, and `routable: false`. It has no active executor, lease issuer, scheduler adapter, credential adapter, status collector, or cancellation adapter.
- **external not tested**: no Slurm client command, DFT executable, launcher, module system, container, SSH session, remote filesystem, or cluster was used.

The existing `local` and `openpbs` renderer branches are candidate-local synthetic regression surfaces, not activated or externally validated execution routes. The operational manual covers Slurm only.

## Implemented CLI

Run from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-hpc-execution/scripts/hpc_execution_cli.py \
  validate-request \
  --request skills/dft-hpc-execution/fixtures/slurm-request.json

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-hpc-execution/scripts/hpc_execution_cli.py \
  render-dry-run \
  --request skills/dft-hpc-execution/fixtures/slurm-request.json \
  --decision skills/dft-hpc-execution/fixtures/slurm-decision.json \
  --lease skills/dft-hpc-execution/fixtures/slurm-lease.json \
  --scheduler slurm --at-utc 2026-07-19T00:00:00Z

PYTHONDONTWRITEBYTECODE=1 python3 -B \
  skills/dft-hpc-execution/scripts/hpc_execution_cli.py \
  classify-status \
  --observation skills/dft-hpc-execution/fixtures/scheduler-success-app-failure.json
```

All outputs go to stdout. `render-dry-run` returns script text, a proposed `sbatch` argv, `side_effect_performed=false`, and `scheduler_job_id=null`; it does not create the script file. `classify-status` exit `0` means classification completed, not that the job succeeded—inspect `states.normalized_execution`.

Require `lease_consumed=false`, `workflow_event_emitted=false`, and `external_execution_performed=false` for every candidate command. There is no candidate `execute` subcommand. Build any final structured response as `agent-action-envelope@1.0` and validate it with `tools/validate_agent_answer.py`; do not present the candidate report as that answer contract.

Exit codes are `0` bounded command completed, `2` malformed/contract-invalid input, `3` authorization/state/evidence blocked, and `4` bounded tool failure.

## Manual execution boundary

1. Validate route and contracts. A non-active, null, or blocked route stops the workflow.
2. Match the request, human decision, and single-use lease by exact raw-byte hashes, scope, resources, expiry, and side effects.
3. Render the Slurm dry run and have a human compare every directive, argv item, input/output path, site account/partition/QoS, module/container/launcher choice, and resource value against site policy.
4. Only a separately authorized human or external executor may materialize the reviewed script and type `sbatch`. The candidate cannot do it.
5. Observe active and accounting state with the exact `squeue`, `sacct`, and `scontrol` patterns in the Slurm manual. Preserve native state and application evidence independently.
6. `scancel` is a side effect. Require a fresh human confirmation of job ID, ownership, scope, and consequence before it is typed; observe the post-cancel state afterward.
7. After a terminal event, create `run-manifest@1.0`, then hand it to `$dft-postprocess` and `$dft-campaign-efficiency` manually.

## Failure rules

- `sbatch` returning a job ID proves submission acceptance, not resource allocation, execution, application completion, numerical adequacy, or scientific acceptance.
- Absence from `squeue` is not proof of completion; query accounting and inspect application output.
- Unknown submission outcome blocks resubmission. Automatic retry is forbidden.
- Site defaults are not inferred. An unreviewed account, partition, QoS, launcher, environment, scratch policy, license, or file staging rule blocks real execution.
- Do not record credentials, hostnames, account names, private paths, or unpublished results in candidate artifacts.

## Additional references

- Use [references/operational-playbooks.md](references/operational-playbooks.md) for resource mapping, arrays/dependencies, live observation, failure recovery, and GPU-specific checks.
- Use [references/official-source-index.json](references/official-source-index.json) for the Slurm-only official source set.
- Use [references/scheduler-status-mapping.json](references/scheduler-status-mapping.json) only to normalize supplied observations; preserve unknown native states.
- Use [references/fail-closed-contract.md](references/fail-closed-contract.md), [references/weak-model-decision-table.json](references/weak-model-decision-table.json), and [references/finding-catalog.json](references/finding-catalog.json) for deterministic local gates.
- Use [references/maturity-matrix.json](references/maturity-matrix.json) before promotion or executor integration.
- Use [references/source-pack-seed.json](references/source-pack-seed.json) and [references/source-pack-scope-catalog.json](references/source-pack-scope-catalog.json) for the blocked metadata-only repository, JSON Schema, Slurm, and OpenPBS source boundary; refresh or check them with `scripts/extract_official_source_scope.py`.

The maximum claim while this Skill is development/non-routable is `no_positive_claim`.
