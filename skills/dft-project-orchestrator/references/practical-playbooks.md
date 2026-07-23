# Practical orchestration playbooks

Use these playbooks to turn a research objective into the next bounded repository action. They are operational guidance, not an active executor.

## Freeze the campaign identity first

Record the following before choosing a code or creating work directories:

- anonymized system and structure identity, including the exact structure-manifest hash when available;
- scientific question and observable, with units and the decision tolerance;
- method family, spin/SOC/charge state, pseudopotential or basis provenance, and software-version requirement;
- convergence dimensions that may change the observable;
- intended downstream consumer, such as a band plot, phonon stability decision, or campaign comparison;
- stop, retry, and escalation conditions;
- human owner for scientific choices and side-effect authorization.

If any item is unknown, encode it as an unresolved decision. Do not replace it with a convenient default.

## Start a new calculation campaign

1. Validate the structure record and inspect disorder, occupancy, cell, composition, charge, and periodicity warnings.
2. Choose one active calculation Skill only after matching the physical task to the code's supported evidence profile.
3. Separate the protocol into convergence, production, and downstream stages. Do not let a production run also serve as its own convergence evidence.
4. Create one plan step per immutable input/output handoff. Name the observable and acceptance gate in the step, not only in prose.
5. Make the first side-effecting step depend on an exact execution request, human decision, and lease.
6. After each terminal run, preserve native completion, SCF/geometry convergence, observable convergence, and scientific review as separate states.
7. Route only accepted technical artifacts to postprocessing; route cost evidence independently to campaign efficiency.

## Plan a convergence study

Vary one scientifically relevant dimension at a time unless a coupled design is explicitly justified. Typical dimensions include cutoff/basis quality, k mesh, supercell or q mesh, smearing, vacuum, SCF threshold, force threshold, and finite-size corrections.

For every series, freeze:

- the invariant physics and structure identity;
- the varied parameter and ordered values;
- the target observable and numerical tolerance;
- a minimum stable tail, not only one favorable pair;
- state-change checks, such as magnetic, structural, electronic, or symmetry transitions;
- the selected production point and the evidence linking it to the series.

Stop when the observable is stable under the declared protocol and no unresolved state change invalidates the comparison. Do not stop merely because total energy appears smooth.

## Recover or restart a run

1. Determine whether the scheduler, launcher, application, SCF/optimizer, or storage layer failed.
2. Hash the last accepted input and checkpoint; verify that the restart belongs to the same structure, method, task, and software lineage.
3. Preserve the failed attempt as an immutable event. Do not overwrite it with the restart result.
4. Classify the proposed change as resource-only, numerical-control, or scientific-method change.
5. Reuse a request only when the exact bytes and scope are unchanged. Otherwise create a new request and obtain fresh authorization.
6. Compare the restarted output with an uninterrupted or independently reproducible route when the application does not guarantee restart equivalence.

## Triage a failed campaign

Use this order so that expensive scientific changes do not mask simpler causes:

1. input and provenance identity;
2. environment, executable, license, launcher, and filesystem;
3. scheduler resources and termination reason;
4. application parser and completion markers;
5. numerical convergence and instability;
6. physical model or unsuitable method;
7. downstream artifact and postprocessing validity.

Return the first decisive blocker and one smallest next action. Preserve later suspected causes as unverified hypotheses.

## Assemble a publication-oriented evidence chain

Require a direct path from each proposed claim to the accepted run, normalized dataset, figure/table artifact, convergence evidence, limitations, and human decision. A generated figure with no source hash is not a handoff. A technically completed run with no observable-specific convergence is not publication evidence.

## Operational heuristics

These are practitioner heuristics, not official program rules or evidence that this repository executed a native workflow:

- Run a cheap structural and input sanity stage before allocating production resources.
- Prefer many small, independently auditable convergence steps to one monolithic script.
- Freeze naming and record IDs before submission; mutable directory names are poor lineage identifiers.
- Treat repeated identical failures as a signal to revisit the model or workflow, not as permission for unbounded retries.
- Re-estimate storage and wall time before dense bands, phonons, trajectories, or wavefunction-heavy postprocessing.
- Record rejected protocols and negative results when they explain why the accepted route is credible.
