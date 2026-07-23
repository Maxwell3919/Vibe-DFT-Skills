# Slurm operational playbooks

Use this file with the site's own policy and [slurm-operations.md](slurm-operations.md). Official Slurm syntax does not determine a site's account, partition, QoS, modules, launcher, filesystem, or charging policy.

## Official manual anchors

- `sbatch` options, precedence, arrays, dependencies, exported environment, and output variables: <https://slurm.schedmd.com/sbatch.html>
- job states: <https://slurm.schedmd.com/job_state_codes.html>
- job and step exit codes: <https://slurm.schedmd.com/job_exit_code.html>
- job arrays and element identifiers: <https://slurm.schedmd.com/job_array.html>
- GPU/GRES requests and device visibility: <https://slurm.schedmd.com/gres.html>
- accounting queries: <https://slurm.schedmd.com/sacct.html>

Recheck these pages against the installed Slurm version and site documentation before materializing a script.

## Build the submission packet

Freeze the following as one review unit:

- exact command argv and working directory;
- input, executable, container/module, and checkpoint hashes or immutable identities;
- nodes, tasks, CPUs per task, memory basis, wall time, GPUs/GRES, and placement constraints;
- account, partition, QoS, reservation, and license requirements supplied by the site;
- standard-output/error names containing the job or array identity;
- restart, signal, requeue, timeout, and scratch-staging policy;
- expected outputs and the application completion markers that will be checked later.

Check command-line options, `SBATCH_*` environment variables, and `#SBATCH` directives together because Slurm defines an option-precedence order. Reject hidden environment overrides that change reviewed resources or output paths.

## Map resources to the application

| Application shape | Slurm intent to review | Common mismatch |
|---|---|---|
| MPI-only | tasks/ranks across nodes | requesting CPUs but launching the wrong rank count |
| OpenMP-only | one or few tasks with CPUs per task | failing to bind/export the application thread count |
| Hybrid MPI/OpenMP | tasks times CPUs per task | oversubscribing cores or multiplying memory unexpectedly |
| GPU per rank | GPU/GRES plus task-to-device mapping | allocated GPU count does not match ranks or visible devices |
| Memory-bound serial step | explicit memory and one task | using per-CPU memory as if it were per-node memory |

Do not infer whether `--mem`, `--mem-per-cpu`, `--gpus`, `--gres`, or `--gpus-per-task` is correct without checking the site's configured plugins and the application launch model.

## Use arrays and dependencies safely

Use an array only when each element has an immutable index-to-input mapping and independent output namespace. Record the master ID and element ID separately. Throttle concurrency when storage, licenses, or downstream services cannot sustain all elements at once.

Use dependencies to express actual data readiness, not hoped-for success. After a parent finishes, verify the parent application and expected artifacts before trusting the child. A scheduler dependency can order jobs; it does not validate scientific outputs.

## Observe a live job

1. Capture submission output and the exact job identifier without parsing unrelated digits.
2. Use `squeue` for active state, reason, placement, elapsed time, and pending cause.
3. Use `scontrol show job` when the allocation, dependency, environment, requeue, or node details are needed.
4. Use `sacct` after or near termination for state, exit code, elapsed time, CPU time, memory, and TRES where accounting provides them.
5. Inspect application stdout/stderr and program-specific completion/convergence evidence.
6. Reconcile scheduler state, process exit, application state, expected files, and checkpoint state before selecting the next action.

Absence from `squeue` is an unknown terminal state until accounting or site evidence resolves it.

## Recover from common failures

| Observation | First evidence to collect | Do not assume |
|---|---|---|
| pending too long | pending reason, requested resources, policy limits | the partition is broken |
| out of memory | scheduler state, MaxRSS/TRES, application allocator output | more nodes will fix per-rank memory |
| time limit | checkpoint integrity, last completed stage, I/O tail | resubmitting the same wall time will progress |
| node failure/preemption | state/reason, requeue history, checkpoint lineage | application output is complete |
| nonzero exit | batch-script exit, step exits, signal, application log | scheduler failure caused it |
| completed state but bad output | application markers and scientific gates | `COMPLETED` means the calculation is valid |
| unknown submit result | controller/accounting query and idempotency evidence | it is safe to submit again |

Create a fresh request whenever resources, command bytes, scientific input, or retry semantics change.

## GPU-specific checks

Verify the site's GRES/TRES configuration before choosing GPU syntax. Match requested GPU type/count to task placement and inspect the job-step device-visibility environment. Do not record physical device numbers as portable identities; Slurm may remap visible devices for each job step. GPU allocation does not prove the application used the device efficiently or at all.

## Operational heuristics

These are practitioner heuristics, not SchedMD guarantees or native execution evidence:

- Perform a short single-node smoke run before scaling a new executable/build.
- Request enough diagnostic output to identify rank/thread/GPU placement, but keep logs bounded.
- Compare requested, allocated, and actually used resources before tuning performance.
- Separate restart validation from performance benchmarking; restart I/O can distort timing.
- Stage many-small-file workloads deliberately to avoid metadata bottlenecks.
- Cancel only after re-resolving the exact job/array element and checking ownership and consequences.
