# Operational time savers from campaign evidence

Use these patterns to reduce avoidable wall time, core-hours, storage, reruns,
and workflow delay. They are operational controls and bounded pilots, not fixed
scientific parameters. Never weaken an accuracy, convergence, physical-validity,
or scientific-acceptance criterion to claim a saving.

Keep `measured`, `estimated`, and `counterfactual` costs separate. A branch-count
reduction is not a measured wall-time reduction. A shorter unfinished run is not
faster accepted science.

## Apply gates before allocating expensive work

### `STORAGE_AND_SCHEDULER_ADMISSION`

Before submission, resolve the actual filesystem used by the work directory,
scheduler spool, temporary files, and large response artifacts. Check free
blocks, free inodes, node state, drain reason, active writers, and the declared
storage budget.

Block submission when capacity, ownership, or recovery safety is unresolved.
Never turn this gate into an automatic cleanup action.

Evidence requirement: a timestamped host-local receipt and a task-specific
storage estimate. Experience ceiling: bounded failure avoidance; no fixed
capacity threshold or speedup follows from a historical full filesystem.

Falsifier: a changed filesystem, spool, quota, or scheduler topology requires a
new admission profile.

### `DEPLOYMENT_AND_INPUT_PREFLIGHT`

Exercise the final deployed executable, runtime libraries, resolver, schemas,
registries, generated input, working directory, pseudopotential manifest, and
output targets with a read-only or synthetic preflight before a production
allocation.

Freeze a compute-stage terminal receipt before running optional parsing,
plotting, or review stages. Make downstream stages independently retryable so a
deployment failure cannot force a valid parent calculation to be repeated.

Evidence requirement: final-environment preflight bytes and separate
compute/postprocess state gates. Experience ceiling: failure avoidance; the
preflight does not prove that data-dependent postprocessing will pass.

Falsifier: a failure class that cannot be exercised without the real production
artifact requires a later artifact-specific gate.

### `RUNTIME_WORLD_AND_AFFINITY_PREFLIGHT`

For every new code/build, machine, task class, or resource layout, verify the
actual MPI world, OpenMP thread count, pools/images, CPU affinity, requested and
allocated resources, memory, and scratch isolation. An MPI-enabled executable
does not prove an MPI launch.

Run bounded same-input scaling pilots and compare an equal completed work unit,
wall time, core-hours, memory, and output identity. Do not hard-code a rank,
pool, or thread count from a different host or task.

Evidence requirement: at least one complete comparable work unit per layout.
Experience ceiling: campaign-local layout selection until repeated accepted
records support transfer.

Falsifier: a matched pilot with worse wall time, core-hours, memory, I/O, or
scientific output identity.

## Remove only work that is provably redundant

### `ROLE_AWARE_EXACT_DEDUP_BEFORE_EXPENSIVE_BRANCHES`

Before relaxing registries, orientations, or other discrete candidates, remove
only exact equivalents established by a deterministic witness that preserves
species, occupancy, layer roles, orientation, termination, periodicity, and the
declared transformation policy.

Retain every nominal candidate as an alias record, bind it to its
representative, and preserve a complete coverage witness. Do not use geometric
similarity, a weighted score, a cheap energy, or a single registry to discard
unique stability-lane candidates.

Evidence requirement: full nominal-to-representative mapping, deterministic
equivalence witness, and input-order invariance. Report the result as a branch
count reduction until actual accepted costs exist.

Falsifier: any role exchange, source/protocol mismatch, ambiguous mapping, or
different accepted result under the supposedly equivalent protocol.

### `PARENT_ARTIFACT_REUSE_BEFORE_RECOMPUTE`

When a child postprocess or response stage fails, first determine whether the
expensive parent artifact is complete, immutable, inactive, hash-bound, and
compatible with the requested child. Re-run only the failed child when every
structure, code/build, protocol, prefix, mesh, potential identity, and required
artifact matches.

Do not reuse a parent merely because the directory name, job name, or local
ordinal looks familiar.

Evidence requirement: parent manifest, content hashes, compatibility checks,
and an independent child artifact gate. Experience ceiling: bounded recovery;
the avoided parent cost is counterfactual unless both routes were measured.

Falsifier: missing or changing parent bytes, a protocol mismatch, incompatible
artifact semantics, or a failed child validation.

### `LAST_COMPLETED_STATE_RECOVERY`

For iterative geometry or response work, checkpoint only the last state whose
energy, force, response, or other required work unit completed. Bind the
checkpoint to the input, executable, output offset, and protocol.

Never resume from the last printed geometry when its corresponding scientific
work unit did not finish. Make timeout, signal, and cancellation receipts
atomic and cancellation-safe.

Evidence requirement: completed-work marker plus the associated state and
hashes. Experience ceiling: recovery candidate; restart semantics remain
code- and version-specific.

Falsifier: a controlled interrupted/restarted fixture fails to reproduce the
uninterrupted route within the declared gate.

## Shorten the critical path without hiding incomplete work

### `TASK_ISOLATION_AND_PROMOTION_RECEIPTS`

Give independent branches or q tasks distinct work directories, prefixes,
scratch, logs, terminal receipts, and artifact namespaces. Share only immutable
parents. Before downstream promotion, reconcile scheduler state, executable
termination, warnings, expected artifact coverage, weights or mappings, and
hashes.

Task-local cleanup may remove only explicitly manifested child-generated,
reproducible artifacts after confirming no active writer. It must not remove a
shared parent or act as a general storage cleanup mechanism.

Evidence requirement: one receipt per task and a complete aggregate coverage
check. Experience ceiling: failure avoidance; task completion is not scientific
acceptance.

Falsifier: namespace collision, parent deletion, incomplete coverage, or a
nonreproducible aggregate.

### `MEASURED_LONGEST_FIRST_PILOT`

When independent tasks have strongly unequal costs and a fixed number of slots,
collect matched preflight or prior-task timings and simulate
longest-processing-time-first scheduling. Report estimated makespan separately
from measured core-hours.

Use the policy only as a campaign-scoped pilot until an actual replay validates
the predictor. Do not let predicted duration change scientific coverage.

Evidence requirement: canonical task identities, measured comparable timing
features, slot count, actual schedule, and counterfactual simulation.

Falsifier: ranking instability, memory/I/O contention, queue effects, or an
actual replay that does not reduce makespan.

### `CHEAP_QUALIFICATION_BEFORE_SWEEP`

Before expanding a mixer, solver, parallel layout, non-Gamma response, time
step, mesh tier, or other choice across many cases, run the cheapest
representative pilot that can expose its numerical failure. Follow technical
qualification with the cheapest relevant physical or observable gate.

Passing the cheap pilot may route work but cannot replace the production
protocol. A cheaper response mesh or larger time step remains a pilot until
matched higher-fidelity holdouts satisfy the predeclared error and ranking
criteria.

Evidence requirement: one controlled change at a time, full convergence trace,
and a falsifiable holdout gate. Experience ceiling: campaign-local
qualification; no universal mixer, solver, mesh, time step, or speedup.

Falsifier: loss of convergence, force/energy disagreement, drift, ranking
reversal, or an observable outside tolerance.

### `PROMOTION_GATE_BEFORE_DOWNSTREAM`

Before launching an expensive dependent stage, generate a machine-readable
receipt that separates software completion, artifact completeness, numerical
validity, physical validity, postprocess validity, scientific acceptance, and
promotion eligibility.

Treat warnings according to version-matched official semantics and the project
acceptance protocol. A normal exit and downstream files can coexist with a
numerical blocker.

Evidence requirement: explicit expected artifacts, warning/fatal policy,
coverage, protocol identity, and the decision authority. Experience ceiling:
failure avoidance.

Falsifier: a warning class proven harmless for the exact version, protocol, and
observable may be downgraded through reviewed evidence, never silently ignored.

## Control intentional duplication and preserve observability

### `HEDGE_BUDGET_AND_FIRST_VALID_WINS`

Before launching duplicate work, declare whether it is tail-latency insurance
or an independent scientific replication. Bind a maximum wall-time,
core-hour, and storage budget; the launch condition; the first-valid gate; the
authorized disposition of the slower copy; and the evidence preserved before
any cancellation.

Do not infer permission to cancel from the existence of a faster result.

Evidence requirement: predecision hedge policy plus repeated campaign latency
and failure-rate evidence. Experience ceiling: insufficient evidence until the
latency benefit and duplicate cost are measured together.

Falsifier: repeated comparable campaigns show that hedging reduces the declared
tail-latency objective enough to justify its measured duplicate cost, or that
both results are required independent evidence.

### `COST_OBSERVABILITY_MINIMUM`

Persist cancellation-safe, privacy-safe receipts for:

- submit, start, and end timestamps plus monotonic elapsed time;
- requested and allocated resources, ranks, threads, pools, affinity, and
  runtime-library identity;
- scheduler state, exit code, signal, and wrapper state;
- stage wall time, core-hours, peak memory, I/O, storage delta, restarts, and
  repeated work when observable;
- input, executable, parent, output, and required-artifact hashes;
- SCF, ionic, force, response, or trajectory work-unit counts;
- all seven state gates and the human decision lineage.

Record unavailable metrics as unavailable. Do not replace measured CPU usage
with `ranks × wall` without labeling it nominal or allocated.

Evidence requirement: a receipt that survives normal exit, timeout, signal, and
cancellation. This pattern improves future decisions; it does not itself prove
a speedup.
