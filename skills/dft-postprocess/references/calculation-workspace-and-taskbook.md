# Postprocessing milestone and taskbook route

When outputs belong to a managed calculation workspace, apply
`docs/calculation-workspace-and-taskbook.md`. Read only an identified terminal
attempt under `03-runs/`; never write derived files into the native run
directory.

Write normalized tables and metadata under `04-derived/<stage-id>/`, figures
under `05-figures/<stage-id>/`, and human-readable summaries under
`06-reports/`. Preserve versioned labels instead of overwriting recorded bytes.
Record validated normalized output as a typed `data` milestone before recording
a dependent `figure`; record the report separately.

In `milestone-review`, append every produced data, figure, or report milestone
as `pending-review` and pause. A later approval revision confirms review of
those bytes only; it does not establish parsing correctness, physical validity,
or scientific acceptance. In silent mode, append `not-required` updates without
routine pauses. Run `check` before handoff.
