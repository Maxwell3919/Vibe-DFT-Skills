# Main Branch Protection Policy

The `main` branch is the release and lifecycle source of truth. Repository settings should enforce the following controls.

## Required pull-request controls

- Require a pull request before merging.
- Require at least one explicit approval.
- Dismiss stale approvals when new commits are pushed.
- Require review from CODEOWNERS.
- Require all review conversations to be resolved.
- Prevent the most recent pusher from being the sole approving reviewer when the repository has more than one eligible reviewer.

## Required status checks

Require the `validate` workflow and, as CI is split, require each of the following logical checks:

- registry and contracts;
- active Skill tests;
- development Skill offline tests;
- repository audit;
- bundle semantic validation;
- privacy and restricted-content validation;
- active-only distribution validation;
- documentation and whitespace checks.

Until the split checks exist, the existing `validate / test` result is the minimum required status check.

Require branches to be up to date before merging when a change affects contracts, registries, lifecycle, routing, execution boundaries, or releases.

## History and administrative controls

- Block force pushes.
- Block branch deletion.
- Restrict direct pushes to `main`.
- Apply rules to administrators where operationally possible.
- Do not allow bypass for lifecycle promotion, release, contract-major, privacy, or authorization changes.
- Prefer squash merge or rebase merge for focused pull requests; do not use a merge strategy to hide unrelated changes.

## Sensitive changes

The following changes require a dedicated pull request and explicit owner review:

- `development -> active` promotion or active demotion;
- contract-major changes;
- privacy, license, authorization, execution, lease, cancellation, or recovery semantics;
- source-tree hash or activation evidence changes;
- active-only distribution changes;
- release and baseline records;
- GitHub Actions permissions or third-party action changes.

## Verification

Repository settings are external to Git history. After configuring protection, record the following in a reviewed issue, pull request, or release checklist:

- ruleset or branch-protection name;
- protected branch pattern;
- required checks;
- required approvals;
- CODEOWNERS enforcement state;
- force-push and deletion state;
- administrator bypass state;
- verification date and reviewer.

This file defines the intended settings. Its presence does not prove that GitHub branch protection has been configured.
