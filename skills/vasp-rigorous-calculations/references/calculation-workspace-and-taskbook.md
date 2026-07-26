# VASP calculation workspace and taskbook route

Read `docs/calculation-workspace-and-taskbook.md` and record the user's
explicit `off`, `silent-update`, or `milestone-review` selection before the
first calculation side effect. Taskbook mode controls pauses, not execution
authority or scientific decisions.

Store one attempt under `03-runs/<stage-id>/<attempt-id>/`. Keep `INCAR`,
`POSCAR`, `KPOINTS`, the runtime-only `POTCAR`, stdout/stderr, restart ancestry,
scheduler identity, and audit reports together at that attempt root. Separate
source structures, prepared inputs, derived tables, and figures. Never move an
active VASP workdir. Verify the workspace and taskbook chain before each
milestone handoff.
