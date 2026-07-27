# Orchestration workspace and taskbook route

Apply `docs/calculation-workspace-and-taskbook.md` as the repository-wide
operational protocol. Preserve the user's explicit `off`, `silent-update`, or
`milestone-review` choice with the immutable workflow plan before a calculation
side effect.

The taskbook is a revisioned progress and review aid. It never replaces or
mutates a workflow plan, execution request, decision, lease, run manifest, or
scientific decision. In review mode, bind initial approval to the exact
workflow-plan and generated input-set hashes. A later plan or input change
requires new identities and a new request; it cannot inherit the earlier
approval.

Create one attempt identity per launch/retry. Route stable artifacts through the
typed `planning`, `structure`, `input`, `execution`, `data`, `figure`, and
`report` milestones. In review mode, append `pending-review` and pause before a
later approval revision. In silent mode, update without routine pauses only
within existing route and execution authority.

This development Skill may plan the layout but does not initialize a production
workspace, execute work, or authenticate approval.
