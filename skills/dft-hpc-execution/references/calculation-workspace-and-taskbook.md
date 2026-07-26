# HPC workspace and taskbook route

Apply `docs/calculation-workspace-and-taskbook.md` together with the execution
contracts. Record the user-selected taskbook mode before the first calculation
side effect, but never interpret that mode as scheduler authorization, a
lease, site-policy approval, or cancellation approval.

Keep each scheduler submission and retry in a distinct
`03-runs/<stage-id>/<attempt-id>/` directory with its exact input identity,
argv, scheduler identity, stdout/stderr, exit state, restart ancestry, and
audits. Do not move or archive a directory while any process may write it. A
review-mode taskbook pause is additional to all execution gates. This
development Skill does not submit work or authenticate a review.
