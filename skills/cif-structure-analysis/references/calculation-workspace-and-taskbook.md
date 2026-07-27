# Structure milestone and taskbook route

When analysis belongs to a managed calculation workspace, apply
`docs/calculation-workspace-and-taskbook.md`. Preserve source CIF and every
selected or transformed structure under `01-structures/` with distinct labels;
do not replace the provenance baseline in place.

After deterministic analysis passes, record stable structure bytes plus the
structure manifest/summary as a typed `structure` milestone. In
`milestone-review`, append it as `pending-review` and pause; only a later
revision may record user approval. A reviewed structure is approved as the next
planned input, not proven stable, lowest-energy, or scientifically accepted.

Do not register PNG projections as structure evidence. If useful for review,
record them separately as `figure` artifacts after their source structure and
display mapping are traceable. Run the workspace `check` before handoff.
