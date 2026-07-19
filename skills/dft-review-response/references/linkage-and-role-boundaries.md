# Linkage and role boundaries

## Required graph

Each comment has exactly one response. Each response points to exactly one proposed change or one no-change reason. Scientific/method chains bind exactly one present evidence ID and one supported no-positive claim ID. Each change points back to exactly one matching response/comment and repeats the same evidence and claim IDs. Claims and evidence come from the exact supplied claim map; a positive upstream claim requires external bundle verification.

Raw reviewer text and requested-action prose never enter a generated plan or package. The plan retains only comment ID, pseudonymous reviewer label, concern type, content hashes, and `content_redacted=true`.

The graph is append-only: the original comment and claim map are not rewritten. A later manuscript editor creates a changed artifact; a later human author/reviewer records decisions; a later release system submits exact reviewed bytes.

## Roles

| Role | Authority |
| --- | --- |
| Reviewer/editor | Supplies comments; identity is externally authenticated |
| Response planner | Classifies and links supplied records; cannot speak for authors |
| Deterministic CLI | Checks IDs, hashes, coverage, evidence, claims, and draft authority flags |
| Calculation Skill | Produces new technical/numerical evidence after separate authorization |
| Human scientific reviewer | Accepts or rejects bounded claims through a decision record |
| Manuscript editor | Applies authorized changes and produces exact changed-artifact evidence |
| Release owner | Approves final privacy/license/editorial state and external submission |

## Deferred and disagree cases

`defer`, `disagree`, and `clarify` still require evidence and a bounded claim or explicit non-scientific scope. Do not manufacture a new calculation, promise a future result, mark a comment resolved merely because a response was drafted, or label an unverified modification `implemented`/`completed`.
