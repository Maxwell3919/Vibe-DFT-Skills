# Campaign record and taskbook route

When the campaign belongs to a managed calculation workspace, apply
`docs/calculation-workspace-and-taskbook.md`. Read attempt state and immutable
run evidence; do not infer completion or cost from directory names.

Keep the private experience database outside the workspace and Git. Put only an
authorized, privacy-safe campaign summary or export under `06-reports/` and
record it as a typed `report` milestone. If a normalized, non-sensitive cost
table is part of the project evidence, place it under `04-derived/` and record a
separate `data` milestone.

Taskbook approval confirms review of the recorded bytes, not that a speedup is
transferable or a scientific result accepted. Preserve the Skill's evidence and
promotion gates. In review mode, append `pending-review` and pause; in silent
mode, append `not-required`. Run the workspace `check` before handoff.
