# QE calculation workspace and taskbook route

Follow `docs/calculation-workspace-and-taskbook.md` before the first
calculation side effect. Record the user's explicit `off`, `silent-update`, or
`milestone-review` choice; it is not execution authorization.

Use one `03-runs/<stage-id>/<attempt-id>/` directory per QE attempt. Keep the
input, stdout/stderr, `outdir` identity, restart ancestry, scheduler record, and
audit evidence together. Separate prepared inputs, derived data, and figures
into their fixed workspace directories. Do not move or clean a live `outdir`.
Run `tools/manage_calculation_workspace.py check` before presenting a
milestone.
