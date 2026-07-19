# Slurm operations manual

All scheduler facts in this file are sourced only from the official SchedMD manuals listed in `official-source-index.json`. The pages were checked on 2026-07-19 and identified themselves as Slurm 26.05 live documentation. A real cluster may run another version and impose site-specific policy.

Every command in this file is **external not tested** for this candidate. None was executed during local validation. The candidate has no scheduler adapter and cannot authorize, materialize, submit, observe, or cancel a job.

## 1. Preconditions

Before any cluster command, a human operator must confirm:

1. installed Slurm client/server version and the site's own documentation;
2. exact job script bytes and SHA-256 match the reviewed dry-run report;
3. exact argv, input availability, output locations, working directory, file staging, and restart policy;
4. account, partition, QoS, reservation, modules/container, launcher, licenses, scratch, memory, CPU/GPU, and time limit;
5. unexpired execution authorization and single-use attempt scope;
6. no unresolved prior submission outcome and no automatic retry.

The candidate renderer does not infer any of these site values.

## 2. Materialize and verify the reviewed script

`render-dry-run` returns `rendered_script` and `rendered_script_sha256` in JSON but does not create a file. Materialization is **design-only** in this repository. A separately trusted executor or human operator must write exactly those bytes to a new script path, compute its SHA-256, compare it with the report, and refuse overwrite or substitution.

Do not interpolate shell variables into `#SBATCH` directives expecting Slurm to expand them. The official `sbatch` manual says directive text is read literally, and directives after the first non-comment/non-whitespace script line are not processed.

## 3. Submit once

After the explicit human submission confirmation:

```bash
submission="$(sbatch --parsable "$SCRIPT")"
job_id="${submission%%;*}"
```

`sbatch --parsable` prints the job ID and, when present, cluster name separated by a semicolon. Errors still go to stderr. Validate that `job_id` has the expected site-supported form before recording it.

Official semantics to preserve:

- `sbatch` returning zero means the script was transferred to the controller and assigned a job ID; it may remain pending.
- `sbatch` does not move user files other than the batch script.
- A job ID is submission evidence, not execution, application completion, or scientific evidence.
- Do not call `sbatch` repeatedly from a polling/retry loop.

Record the exact stdout, stderr, exit status, submission time, script hash, request/decision/lease hashes, job ID, optional cluster name, and attempt ID in an external execution record. The current candidate cannot create that production record.

## 4. Observe active state with `squeue`

Use an explicit job filter and machine-readable delimiter:

```bash
squeue --noheader --jobs="$JOB_ID" --format='%i|%T|%R'
```

The fields are job ID, extended state, and reason/node list. Preserve the native text. A typical active observation may be `PENDING` or `RUNNING`; consult the official state-code page rather than inventing a mapping.

Do not poll tightly or indefinitely. The official manuals warn that repeated client RPCs can degrade `slurmctld`; use a site-approved bounded interval and stop condition. This repository does not implement such a monitor.

No line from `squeue` is ambiguous: the job may have become terminal, moved to accounting, be hidden by policy, or the query may have failed. Absence is not proof of completion.

## 5. Observe accounting and terminal state with `sacct`

```bash
sacct --noheader --parsable2 --jobs="$JOB_ID" \
  --format=JobIDRaw,State,ExitCode,Elapsed,AllocTRES
```

`--parsable2` produces pipe-delimited output without a trailing delimiter. Preserve allocation and step rows rather than silently choosing the most favorable row. Requeues or duplicate job records may require the official `--duplicates` behavior and lineage review.

`COMPLETED` is a Slurm state indicating zero exit code on all nodes. It is still only scheduler/process evidence. Inspect the engine's output audit for application completion, warnings, numerical gates, and scientific limitations.

States such as `FAILED`, `CANCELLED`, `TIMEOUT`, `OUT_OF_MEMORY`, `NODE_FAIL`, or `PREEMPTED` must remain explicit. Never normalize them to success because partial output exists.

## 6. Inspect details with `scontrol`

```bash
scontrol --oneliner show job "$JOB_ID"
```

The official manual documents `scontrol [OPTIONS] [COMMAND]`, `--oneliner`, and `show job <jobid>`. Relevant fields include current `JobState` and `ExitCode`. Availability and detail can depend on ownership, privilege, private-data policy, and job lifetime.

Use `scontrol` to resolve a specific ambiguity, not as an unbounded polling loop. Preserve the command exit status and raw observation.

## 7. Cancel only after a fresh human confirmation

Cancellation changes cluster state. Confirm exact job ID, cluster, owner, request/lease lineage, current state, scope, data-loss/staging consequences, and the reason. Then a human may use interactive confirmation:

```bash
scancel --interactive "$JOB_ID"
```

The official manual says `scancel` signals or cancels Slurm-controlled jobs/steps; without `--signal`, the specified job is terminated. `--interactive` asks for confirmation for each job ID. Do not use broad user, partition, account, or state filters in an automated candidate workflow.

After the command, capture exit status/stdout/stderr and make fresh observations:

```bash
squeue --noheader --jobs="$JOB_ID" --format='%i|%T|%R'
sacct --noheader --parsable2 --jobs="$JOB_ID" \
  --format=JobIDRaw,State,ExitCode,Elapsed,AllocTRES
scontrol --oneliner show job "$JOB_ID"
```

A successful `scancel` invocation is not itself proof of the final state. Preserve any uncertainty and do not reuse a consumed lease.

## 8. Reconcile with application evidence

For QE, VASP, CP2K, or SIESTA, keep these layers independent:

1. submission: exact `sbatch` result and job ID;
2. scheduler: native `squeue`/`sacct`/`scontrol` observations;
3. process: exit code/signal for allocation and relevant steps;
4. application: engine-specific completion markers, fatal/warning scan, input/output identity;
5. numerical/scientific: convergence and task-specific evidence;
6. human decision: acceptance/rejection and release authority.

Only the appropriate active calculation Skill can audit layer 4 for its supported surface. Layers 5 and 6 require their own evidence and human review.

## 9. Official sources

- `sbatch`: <https://slurm.schedmd.com/sbatch.html>
- `squeue`: <https://slurm.schedmd.com/squeue.html>
- `sacct`: <https://slurm.schedmd.com/sacct.html>
- `scontrol`: <https://slurm.schedmd.com/scontrol.html>
- `scancel`: <https://slurm.schedmd.com/scancel.html>
- job state codes: <https://slurm.schedmd.com/job_state_codes.html>

Recheck the matching official manual for the installed Slurm version and apply site policy before a real command.
