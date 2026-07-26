# CP2K calculation workspace and taskbook route

Apply the repository protocol in
`docs/calculation-workspace-and-taskbook.md` before the first calculation side
effect. The user must explicitly select `off`, `silent-update`, or
`milestone-review`; this choice controls taskbook pauses only.

Keep each CP2K attempt in its own `03-runs/<stage-id>/<attempt-id>/` directory.
Preserve its main input, included files, output, restart ancestry, scheduler
identity, and audit reports together. Put prepared inputs in `02-inputs`,
derived tables in `04-derived`, and figures in `05-figures`. Never reorganize
an active directory. Use `tools/manage_calculation_workspace.py check` before a
review handoff.
