# Contributing to Vibe-DFT-Skills

Vibe-DFT-Skills treats scientific interfaces, lifecycle state, evidence lineage, and side-effect boundaries as reviewed code. A passing parser or successful external calculation is not sufficient by itself to promote a capability.

## Contribution scope

Keep each pull request focused on one reviewable concern. Preferred pull-request classes are:

- one contract or contract migration;
- one registry or routing change;
- one Skill implementation or correction;
- one fixture and its provenance record;
- one postprocessing adapter;
- one CI or governance change;
- one lifecycle promotion;
- one official-source snapshot refresh.

Do not combine lifecycle promotion, unrelated Skill changes, broad contract edits, source refreshes, and CI restructuring in the same pull request.

## Evidence labels

Every scientific or engineering statement in a pull request should be distinguishable as one of:

- repository-observed fact;
- external-source claim;
- tested behavior;
- inference;
- temporary assumption;
- unresolved item.

Repository tests establish only the behavior they exercise. They do not establish native third-party execution, numerical convergence, physical validity, or scientific acceptance unless a separate evidence record says so.

## Lifecycle changes

The allowed lifecycle sequence is:

```text
planned -> development -> active
```

A lifecycle change must be explicit. Installing an executable, finding an official manual, adding a source directory, or passing synthetic tests must not change lifecycle automatically.

A `development -> active` promotion must be submitted as a dedicated pull request and satisfy `docs/lifecycle-promotion-policy.md`.

## Contracts and lineage

When adding or changing a contract:

1. preserve a unique contract identity and version;
2. declare the document kind and record identity semantics;
3. keep all references offline-resolvable;
4. add positive, negative, and mutation fixtures;
5. state whether the change affects claim ceilings, handoff, execution, privacy, or lifecycle;
6. provide a migration for incompatible historical records;
7. never fill missing scientific evidence during migration.

A downstream record must not silently replace, mutate, or reinterpret its parent record.

## Scientific software and artifacts

Do not commit:

- credentials, tokens, SSH material, private hosts, accounts, scheduler identities, or real local/server paths;
- licensed or restricted potential contents such as VASP POTCAR data;
- raw private calculation trees;
- unpublished numerical results unless an explicit repository decision permits a sanitized fixture;
- wavefunctions, checkpoints, large trajectories, databases, or model weights unless a reviewed policy explicitly allows them;
- copied third-party manuals or source material outside their redistribution terms.

Use anonymized identifiers in fixtures and examples. Preserve only the metadata, hashes, provenance, and minimal redistributable bytes needed for deterministic validation.

## Deterministic behavior

Put deterministic gates in tested code rather than prose. A gate must:

- fail closed when required evidence is missing;
- emit stable finding codes;
- avoid network access unless the command explicitly declares network-read behavior;
- avoid modifying calculation inputs or scientific acceptance criteria;
- separate execution completion, numerical convergence, physical review, and scientific acceptance.

## Required local validation

Run before requesting review:

```text
python3 tools/run_tests.py
python3 tools/run_development_tests.py
python3 tools/validate_all_skills.py
python3 tools/audit_repository.py
git diff --check -- . ':(exclude)skills/qe-rigorous-calculations/references/official-*'
```

Also inspect `git status` and the staged diff for private paths, credentials, restricted artifacts, runtime databases, and raw scientific outputs.

## Pull-request description

A pull request should state:

- the problem and failure mode;
- files and interfaces changed;
- files and interfaces intentionally not changed;
- positive and negative tests;
- mutation or adversarial tests where applicable;
- evidence and fixture provenance;
- lifecycle impact;
- claim-ceiling impact;
- privacy and license impact;
- rollback method;
- unresolved limitations.

## Review requirements

Changes to the following areas require explicit owner review:

- `contracts/`;
- `registry/`;
- `tools/` validators and execution boundaries;
- `.github/workflows/`;
- lifecycle state;
- release and baseline records;
- scientific fixtures used to support maturity claims.

The implementer must not treat their own implementation result as the final scientific acceptance decision.
