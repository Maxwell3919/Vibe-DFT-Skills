# CP2K calculation workspace and taskbook route

Apply `docs/calculation-workspace-and-taskbook.md`. Record the user's explicit
`off`, `silent-update`, or `milestone-review` choice before the first
calculation side effect. The choice controls taskbook pauses only.

Place a complete CP2K input set under one
`02-inputs/<stage-id>/<input-set-id>/`: main input, included files, coordinates,
basis/potential metadata or runtime files, and restart inputs. Generate
`input-set.json`. In review mode, freeze it with the workflow plan and obtain an
exact-hash initial review decision before `init-attempt`.

Give every launch or retry a new `03-runs/<stage-id>/<attempt-id>/`. Keep the
main input, include tree, output, stderr, restart ancestry, scheduler identity,
run manifest, and audits with that attempt. Append `active` only after a
separately authorized executor actually starts it; append a terminal event from
observed CP2K and scheduler evidence.

Record stable geometry as a `structure` milestone, run evidence as `execution`,
normalized results as `data`, and plots as `figure`. Never reorganize an active
attempt. Run `check` before a handoff and `check --require-quiescent` before any
move, cleanup, or archive.
