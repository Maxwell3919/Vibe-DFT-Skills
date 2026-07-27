# SIESTA calculation workspace and taskbook route

Use the canonical workflow in `docs/calculation-workspace-and-taskbook.md`.
Before any calculation side effect, record whether the user selected `off`,
`silent-update`, or `milestone-review`. The selection never grants execution
or scientific acceptance.

Give every SIESTA attempt a distinct
`03-runs/<stage-id>/<attempt-id>/` directory. Preserve its direct FDF, included
files, pseudopotential manifest, runtime-only pseudopotentials, output,
restart lineage, and audits together. Keep structures, prepared inputs,
derived data, and figures in their designated directories. Never reorganize a
directory while SIESTA may be writing it, and run the workspace `check` before
review.
