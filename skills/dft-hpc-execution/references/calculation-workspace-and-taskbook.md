# HPC workspace and taskbook route

Apply `docs/calculation-workspace-and-taskbook.md` together with every execution
contract. Taskbook selection, initial review approval, and milestone approval
never substitute for an execution request, human decision, single-use lease,
site-policy review, scheduler authority, or cancellation confirmation.

Require a generated `input-set.json` and, in review mode, its exact-hash initial
review approval before preparing an attempt. Keep each scheduler submission and
retry in a new `03-runs/<stage-id>/<attempt-id>/` with its materialized input
identity, argv, scheduler identity, stdout/stderr, application exit evidence,
restart ancestry, run manifest, and audits.

Append `active` only after external observation confirms the submitted attempt
is active. Unknown submission outcome blocks retry. Append a terminal event only
after scheduler and application evidence are reconciled; neither one implies
the other. Do not move or archive a directory while any process may write it.
Require `check --require-quiescent` before reorganization.

This development Skill does not submit work, write a production taskbook, or
authenticate user review.
