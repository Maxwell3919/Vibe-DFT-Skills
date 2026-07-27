# Calculation Workspace and Dynamic Taskbook

Use this repository-wide protocol for every new calculation-side workspace that
the user wants kept orderly and reviewable. It organizes operational files and
progress evidence around the immutable scientific and execution contracts. It
does not replace a `workflow-plan`, an `execution-request`, human execution
authority, site policy, a run manifest, or a scientific decision.

## Select the collaboration mode

Before the first calculation side effect, have the user select exactly one
mode:

- `off`: create and validate the orderly workspace without a taskbook;
- `silent-update`: maintain the taskbook and attempt history automatically
  without routine review pauses;
- `milestone-review`: require an initial review of the exact workflow plan and
  input set, then pause on each configured structure, input, execution, data,
  figure, or report milestone.

Do not infer the choice from silence. Record the selection time. The choice
controls taskbook review pauses only. It never grants execution, submission,
cancellation, destructive-change, scientific-route-change, or scientific
acceptance authority. In silent mode, continue only within authority and a
scientific route already established outside this taskbook.

## Keep one identity per directory

Create one workspace per anonymized case and scientific protocol:

```text
00-governance/
  workspace-manifest.json
  plans/
  taskbook-current.json
  taskbook-revisions/
01-structures/
02-inputs/<stage-id>/<input-set-id>/
  input-set.json
03-runs/<stage-id>/<attempt-id>/
  00-attempt/
    attempt-manifest.json
    events/
  <materialized native input files>
  <native outputs and restart files>
04-derived/<stage-id>/
05-figures/<stage-id>/
06-reports/
90-archive/
```

Use `01-structures` for source and staged structures. Put each complete,
launch-ready native input set under one new
`02-inputs/<stage-id>/<input-set-id>/` identity. Never change recorded input
bytes in place; create a new input-set ID. The input-set manifest hashes every
file and carries no execution permission.

Use one `03-runs/<stage-id>/<attempt-id>/` for exactly one launch or retry.
`init-attempt` materializes the recorded input bytes into that attempt without
mixing another attempt's files. Keep native filenames and code-required relative
paths. Preserve stdout, stderr, restart ancestry, scheduler identity, terminal
run record, and audits with the attempt. A retry always receives a new attempt
ID.

Never rename, move, clean, or archive a directory while its latest immutable
attempt event is `active` or while any external process may still write there.
`check --require-quiescent` must pass before reorganizing or archiving. An
unknown external state is not quiescent merely because no process appears in a
local process listing; reconcile it and append the correct terminal event first.

## Bind initial review to exact bytes

In `milestone-review`, initialization starts with
`initial_execution_review.state=awaiting-request`. Prepare:

1. an immutable `workflow-plan` under `00-governance/plans/`;
2. a generated `input-set.json` that hashes all launch inputs.

`request-initial-review` records exactly one workflow-plan artifact and one
input-set artifact in a new taskbook revision and returns
`pause_required=true`. Present those files and the returned revision hash to the
user. Do not initialize an executable attempt yet.

After actual review, pass the exact returned SHA-256 to
`decide-initial-review`. A stale hash is rejected. Approval records the reviewed
revision and its hash; requested changes close the gate. If the plan or any
input changes, use a new plan/input-set identity and request review again. Never
reuse an earlier approval for different bytes.

This is review readiness, not execution authorization. After approval, still
apply the calculation Skill's input gates, the execution request/decision/lease
route, and the target site's policy before any external execution side effect.
The tool records an operator assertion that the user reviewed the bytes; it
cannot authenticate a human.

## Maintain the dynamic taskbook

Each taskbook update appends strict UTF-8 JSON under
`taskbook-revisions/`. Revisions are contiguous, timestamped, and hash-linked.
Never edit an existing revision. `taskbook-current.json` is only the replaceable
latest copy and is not immutable evidence.

Every stage records:

- stable `stage_id`, title, and milestone kind;
- status, review state, summary, next action, and update time;
- stable relative artifact labels, byte counts, and SHA-256 values;
- a review note when approval is asserted.

Use the following milestone/artifact pairings:

| Milestone kind | Required artifact at `pending-review` or `completed` |
|---|---|
| `planning` | `workflow-plan` under `00-governance/plans/` |
| `structure` | `structure` under `01-structures/` |
| `input` | `input-set` under `02-inputs/` |
| `execution` | `run-record` under `03-runs/` |
| `data` | `dataset` under `04-derived/` |
| `figure` | `figure` under `05-figures/` |
| `report` | `report` under `06-reports/` |

Record only existing, stable artifacts. Do not record an actively changing
output as terminal evidence. Do not fabricate a structure, dataset, or figure
to satisfy a milestone. A recorded artifact label is immutable: changed bytes
must be preserved under a new label and recorded in a new revision.

In `milestone-review`, first record a produced milestone as
`status=pending-review, review_state=pending-review` and pause. Only a later
revision may record `status=completed, review_state=approved`, with a review
note. The tool rejects direct approval without an earlier pending revision and
rejects reopening a completed stage. In `silent-update`, always use
`review_state=not-required`; this means no taskbook pause, not scientific
acceptance.

## Command sequence

Initialize the workspace:

```bash
python3 tools/manage_calculation_workspace.py init CASE_ROOT \
  --case-id case-anon-001 --protocol-id protocol-pbe-v1 \
  --objective "Converge the named observable" \
  --review-mode milestone-review \
  --selected-utc 2026-07-26T10:00:00Z
```

After writing native inputs under a new input-set directory, hash them:

```bash
python3 tools/manage_calculation_workspace.py create-input-set CASE_ROOT \
  --stage-id static-stage --input-set-id inputs-v001 --engine-id qe \
  --input main-input=02-inputs/static-stage/inputs-v001/calculation.in \
  --input pseudopotential=02-inputs/static-stage/inputs-v001/element.upf \
  --at-utc 2026-07-26T10:10:00Z
```

Request and record initial review:

```bash
python3 tools/manage_calculation_workspace.py request-initial-review CASE_ROOT \
  --workflow-plan 00-governance/plans/workflow-plan.json \
  --input-set 02-inputs/static-stage/inputs-v001/input-set.json \
  --summary "Present the frozen plan and input bytes for review" \
  --at-utc 2026-07-26T10:20:00Z

python3 tools/manage_calculation_workspace.py decide-initial-review CASE_ROOT \
  --decision approved --expected-taskbook-sha256 <REQUEST_REVISION_SHA256> \
  --review-note "User reviewed this exact plan and input set" \
  --at-utc 2026-07-26T10:30:00Z
```

Materialize one attempt, then append observed lifecycle events. Typing or
submitting the executable command remains a separate authorized action:

```bash
python3 tools/manage_calculation_workspace.py init-attempt CASE_ROOT \
  --stage-id static-stage --attempt-id attempt-001 --engine-id qe \
  --input-set 02-inputs/static-stage/inputs-v001/input-set.json \
  --summary "Materialize the reviewed input bytes" \
  --at-utc 2026-07-26T10:40:00Z

python3 tools/manage_calculation_workspace.py append-attempt-event CASE_ROOT \
  --stage-id static-stage --attempt-id attempt-001 --state active \
  --summary "The external executor reported this attempt active" \
  --at-utc 2026-07-26T11:00:00Z

python3 tools/manage_calculation_workspace.py append-attempt-event CASE_ROOT \
  --stage-id static-stage --attempt-id attempt-001 --state completed \
  --summary "Recorded terminal application evidence" \
  --artifact run-record=03-runs/static-stage/attempt-001/run-manifest.json \
  --at-utc 2026-07-26T12:00:00Z
```

Record a new figure for review:

```bash
python3 tools/manage_calculation_workspace.py update CASE_ROOT \
  --stage-id figure-ready --stage-title "Convergence figure" \
  --milestone-kind figure \
  --stage-status pending-review --review-state pending-review \
  --summary "Rendered the figure from the recorded normalized dataset" \
  --next-action "Wait for the user's figure review" \
  --artifact figure=05-figures/figure-ready/convergence-v001.svg \
  --at-utc 2026-07-26T12:10:00Z
```

Verify all manifests, input copies, immutable chains, timestamps, review
bindings, artifact bytes, attempt states, and directory identities before every
review handoff:

```bash
python3 tools/manage_calculation_workspace.py check CASE_ROOT
python3 tools/manage_calculation_workspace.py check CASE_ROOT --require-quiescent
```

Do not claim the workspace orderly, the taskbook current, or the workspace safe
to reorganize unless the corresponding current check passes.
