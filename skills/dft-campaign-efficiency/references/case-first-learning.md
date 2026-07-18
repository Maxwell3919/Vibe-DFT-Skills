# Case-first campaign learning

Write the case before designing its permanent format. A failed, stopped, inherited, or partially documented campaign may contain the most valuable efficiency evidence even when it cannot satisfy the latest JSON contract.

## Preserve a minimal evidence kernel

Keep the surrounding narrative free-form, but make these facts unambiguous when available:

- anonymized case and stage ids, parent/child lineage, and observation time;
- code, version/build, task, system class, atom count, and scientific protocol;
- actual inputs or their checksums, scheduler allocation, executable invocation, and required artifacts;
- observed wall time, core-hours, queue wait, memory, storage, restarts, repeated work, and human delay;
- separate state gates for software completion, artifact completeness, numerical validity, physical validity, postprocessing validity, scientific acceptance, and promotion eligibility;
- the decision made, the evidence available at that time, the alternatives, and whether any savings is measured or counterfactual;
- missing evidence, limitations, counterexamples, and the next falsifiable test.

Do not invent unavailable metrics. `Unavailable` is evidence about observability and should influence later instrumentation.

## Reconstruct actual state before interpreting it

Triangulate state from independent evidence:

1. scheduler job id, state, command, and working directory;
2. executable start/end markers and exit evidence;
3. required output artifacts, sizes, timestamps, and checksums when useful;
4. parser, numerical, and scientific validation results;
5. dependency and wrapper state.

A familiar job name can belong to another directory. A README can be stale. A wrapper can fail after the scientific executable finishes. An executable can print a normal completion marker without producing the downstream artifact. Record each state separately.

For active remote campaigns, inspect read-only unless the user explicitly authorizes intervention. Never infer a terminal lesson from an output that is still growing.

## Separate evidence layers

- `official`: documented program meaning, prerequisites, defaults, and supported restart/reuse behavior;
- `observed`: immutable measurements and validation results from a campaign;
- `practice`: inherited local convention that may or may not be validated;
- `analysis`: present interpretation, cost model, counterfactual, or proposed decision rule.

Do not upgrade analysis into observed fact. Do not cite a project failure as proof of universal software behavior.

## Derive a lesson at the narrowest valid scope

Ask what changed, what remained controlled, what scientific gate was preserved, and whether an accepted alternative exists. A failure can justify a cheap preflight or artifact check. It cannot prove that a different production configuration is faster unless that configuration completed under comparable acceptance criteria.

Attach a falsifier to every candidate rule. Examples include a repeated campaign where the preflight ranking fails, a code-version change that alters restart behavior, or a system class where the recommended parallel layout loses efficiency.

## Let structure emerge

After several cases, identify repeated concepts and only then migrate them into schemas, scripts, or stable headings. Preserve the original narrative and migration provenance. A structured record is an index into evidence, not a replacement for it.

When the current schema loses multistage lineage, partial states, curve-valued convergence, or uncertainty, keep the narrative authoritative and open a schema-design item. Never flatten a campaign until a false comparison becomes possible.
