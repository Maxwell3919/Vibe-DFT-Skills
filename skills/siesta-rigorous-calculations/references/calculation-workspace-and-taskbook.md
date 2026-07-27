# SIESTA calculation workspace and taskbook route

Apply `docs/calculation-workspace-and-taskbook.md`. Before any calculation side
effect, record whether the user selected `off`, `silent-update`, or
`milestone-review`. The selection never grants execution or scientific
acceptance.

Place the direct FDF, included files, structure inputs, pseudopotential manifest,
runtime-only pseudopotentials, and selected restart inputs under one
`02-inputs/<stage-id>/<input-set-id>/`; generate `input-set.json`. In review
mode, freeze that exact manifest with the workflow plan and obtain the
hash-bound initial review decision before `init-attempt`.

Give every SIESTA launch or retry a new
`03-runs/<stage-id>/<attempt-id>/`. Preserve native inputs, output, restart
lineage, scheduler identity, run manifest, and audits together. Append attempt
events from observed state. Never reorganize a directory while SIESTA may write
it.

Use typed `structure`, `input`, `execution`, `data`, and `figure` milestones for
stable artifacts. Run `check` before review and `check --require-quiescent`
before moving, cleaning, or archiving any attempt.
