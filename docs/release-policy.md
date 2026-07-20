# Release Policy

## Release objective

A Vibe-DFT-Skills release publishes a reviewed repository state and, when available, an active-only distribution. A release does not by itself establish that external scientific software is installed, natively validated for every task, numerically converged, physically valid, or scientifically accepted.

## Versioning

Use semantic versioning for repository releases:

- patch: compatible corrections, documentation, fixtures, or deterministic-gate fixes that do not change required record semantics;
- minor: compatible new contracts, adapters, active capabilities, or lifecycle promotions;
- major: incompatible contract, identity, privacy, authorization, evidence-lineage, claim-ceiling, or lifecycle semantics.

Baseline tags may use a descriptive suffix, for example:

```text
v0.1.0-architecture-baseline
```

## Required release inputs

A release candidate must identify:

- source commit SHA;
- contract catalog and registry digests;
- active and development Skill lists;
- active software and maturity scope;
- validation commands and results;
- privacy and restricted-content audit result;
- source-tree hashes for released Skills;
- known limitations and blocked routes;
- migration requirements;
- lifecycle promotions since the previous release.

## Required checks

Before tagging a release candidate, run:

```text
python3 tools/run_tests.py
python3 tools/validate_all_skills.py
python3 tools/audit_repository.py
git diff --check -- . ':(exclude)skills/qe-rigorous-calculations/references/official-*'
```

When the corresponding tools are implemented, releases must also require:

- bundle semantic validation;
- privacy and restricted-content validation;
- active and development offline behavior tests;
- active-only distribution validation;
- activation evidence validation;
- dependency and workflow supply-chain checks.

## Lifecycle promotion boundary

A release must not hide a lifecycle promotion inside unrelated changes. Every `development -> active` transition requires a dedicated reviewed pull request and an activation evidence record.

Adding a source directory, installing an executable, refreshing documentation, or passing synthetic tests must not promote a Skill or software identity automatically.

## Release artifacts

A complete release should contain:

- source archive;
- active-only Skill distribution;
- release manifest;
- SHA-256 checksums;
- validation report;
- changelog;
- known limitations;
- migration notes when applicable.

The active-only distribution must exclude development Skill metadata, private runtime records, restricted files, raw calculation trees, unpublished results, credentials, and licensed potential contents.

## Reproducibility and provenance

Generated release artifacts must record:

- source commit;
- build command and tool version;
- Python version;
- registry and contract digests;
- file-level hashes;
- build environment assumptions;
- whether the artifact was generated from the protected branch.

A release artifact must not be edited manually after generation. Any change requires a new build and new digest.

## Revocation and supersession

A release may be marked revoked or superseded when:

- credentials or restricted content were included;
- a routing or side-effect boundary can be bypassed;
- evidence records or hashes are invalid;
- a lifecycle or maturity claim exceeds its evidence;
- a contract migration loses scientific meaning;
- an active-only distribution includes development Skills.

Do not silently replace an existing tag or release asset. Publish a new auditable correction and identify the affected version.

## Baseline records

Historical baseline records are immutable. If a baseline contains an error, create a new baseline or correction record that identifies the superseded field, the reason, and the evidence for the correction.
