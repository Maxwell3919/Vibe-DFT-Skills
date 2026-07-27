# QE calculation workspace and taskbook route

Apply `docs/calculation-workspace-and-taskbook.md`. Record the user's explicit
`off`, `silent-update`, or `milestone-review` choice before the first
calculation side effect; it is not execution authorization.

Place each complete QE input set under one
`02-inputs/<stage-id>/<input-set-id>/`: executable input, pseudopotential
metadata or runtime files, referenced parent/restart identities, and any launch
wrapper that is itself reviewed. Generate `input-set.json`. In review mode,
freeze it with the workflow plan and obtain an exact-hash initial review
decision before `init-attempt`.

Give every launch or retry a new `03-runs/<stage-id>/<attempt-id>/`. Keep input,
stdout, stderr, `prefix`/`outdir` identity, restart ancestry, scheduler identity,
run manifest, and audit evidence together. Never move or clean a live `outdir`.
Append lifecycle events from observed executor/scheduler/application state, not
directory names.

Record stable geometry as `structure`, launch input as `input`, terminal run
evidence as `execution`, normalized results as `data`, and plots as `figure`.
Run `check` before handoff and `check --require-quiescent` before reorganization.
