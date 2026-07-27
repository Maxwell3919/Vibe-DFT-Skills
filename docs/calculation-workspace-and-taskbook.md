# Calculation Workspace and Dynamic Taskbook

Use this repository-wide operational layout for a new calculation campaign when
the user wants calculation-side files kept reviewable. This is bookkeeping
around the immutable scientific and execution contracts; it does not replace a
`workflow-plan`, `execution-request`, human authorization, run manifest, or
scientific decision.

Before the first calculation side effect, ask the user to select exactly one
taskbook mode:

- `off`: create the orderly workspace, but do not maintain a taskbook;
- `silent-update`: maintain revisions automatically and continue through
  ordinary pre-agreed milestones without asking for taskbook review;
- `milestone-review`: stop at every configured structure, input, result, or
  figure milestone until the user reviews it.

Do not infer the mode from silence. Record the user's selection time. A mode
selection controls only taskbook pauses. It never authorizes execution,
submission, cancellation, destructive changes, scientific-route changes, or
scientific acceptance.

## Workspace layout

Create one workspace per anonymized case and protocol:

```text
00-governance/
  workspace-manifest.json
  taskbook-current.json
  taskbook-revisions/
01-structures/
02-inputs/<stage-id>/
03-runs/<stage-id>/<attempt-id>/
04-derived/<stage-id>/
05-figures/<stage-id>/
06-reports/
90-archive/
```

Keep the native input filenames required by a calculation code together at the
root of one attempt directory. Never mix files from different attempts in one
directory. Do not rename, move, clean, or archive an active working directory.
After an attempt becomes terminal, preserve its native input, stdout, stderr,
restart ancestry, scheduler identity, and audit reports together.

Use `01-structures` for source and staged structures, `02-inputs` for generated
input sets before launch, `03-runs` for immutable attempt identities,
`04-derived` for extracted tables and normalized data, `05-figures` for plots
bound to those data, and `06-reports` for human-readable summaries. Archive only
after checking that no process is writing and all references remain resolvable.

## Taskbook rules

The taskbook is an operational format maintained by
`tools/manage_calculation_workspace.py`; it is not a registered cross-Skill
interface. Each update creates a new UTF-8 JSON revision. Never edit an existing
revision. `taskbook-current.json` is only the replaceable latest copy and may
not be used as immutable evidence.

Every revision records:

- anonymized case and protocol identities;
- selected review mode and selection time;
- revision number, update time, and the exact hash of the previous revision;
- stage state, update summary, review state, and timestamp;
- relative artifact labels plus exact byte count and SHA-256;
- explicit limitations.

Record only existing, stable artifacts. Do not fabricate a structure, dataset,
or figure to satisfy a milestone. Do not record an actively changing output as
terminal evidence. Never overwrite a recorded artifact label: a later byte
change makes `check` fail, so preserve the old bytes and record the new stable
bytes under a new relative label in a new revision.

For `milestone-review`, record a produced milestone as `pending-review` and
pause. Only after the user actually reviews it may an update record
`review_state=approved`; the tool records the operator assertion but cannot
authenticate the human. `changes-requested` returns the stage to work. In
`silent-update`, use `not-required` and continue only within the already agreed
scientific route and execution authority.

## Commands

Initialize a reviewable campaign:

```bash
python3 tools/manage_calculation_workspace.py init CASE_ROOT \
  --case-id case-anon-001 --protocol-id protocol-pbe-v1 \
  --objective "Converge the named observable" \
  --review-mode milestone-review \
  --selected-utc 2026-07-26T10:00:00Z
```

Record a stable structure milestone:

```bash
python3 tools/manage_calculation_workspace.py update CASE_ROOT \
  --stage-id structure-ready --stage-title "Initial structure" \
  --stage-status pending-review --review-state pending-review \
  --summary "Prepared the auditable starting structure" \
  --artifact structure=01-structures/input.cif \
  --at-utc 2026-07-26T11:00:00Z
```

After actual user review, append approval without changing the earlier revision:

```bash
python3 tools/manage_calculation_workspace.py update CASE_ROOT \
  --stage-id structure-ready --stage-title "Initial structure" \
  --stage-status completed --review-state approved \
  --summary "User approved the recorded structure milestone" \
  --review-note "Approved for the next planned stage" \
  --at-utc 2026-07-26T11:30:00Z
```

Verify the directory set, revision chain, current copy, timestamps, and all
recorded artifact bytes:

```bash
python3 tools/manage_calculation_workspace.py check CASE_ROOT
```

Run `check` before every user review handoff and before claiming that the
calculation workspace is orderly or that the taskbook is current.
