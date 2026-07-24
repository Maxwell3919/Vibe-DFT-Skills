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
- official-document bundle state for every source-backed Skill;
- source-tree hashes for released Skills;
- known limitations and blocked routes;
- migration requirements;
- lifecycle promotions since the previous release.

## Required checks

Before tagging a release candidate, run:

```text
python3 tools/run_tests.py
python3 tools/run_development_tests.py
python3 tools/validate_all_skills.py --baseline-ref <trusted-base-ref>
python3 tools/validate_all_skills.py --strict-release --baseline-ref <trusted-base-ref>
python3 tools/audit_repository.py
python3 tools/build_active_only_distribution.py build --root . --output <candidate-active.tar> --require-clean-commit
python3 tools/build_active_only_distribution.py verify <candidate-active.tar> --extract-to <empty-directory>
git diff --check -- . ':(exclude)skills/qe-rigorous-calculations/references/official-*'
```

`tools/run_development_tests.py` is a maintenance-only regression lane. It
compiles every source-backed development Skill and runs only canonical local
tests that are present in the reviewed maintenance allowlist. Check hooks must
also explicitly declare an offline `--check` contract. New or unreviewed hooks
are reported and skipped rather than executed implicitly; inspect the stable
command plan with `python3 tools/run_development_tests.py --list`. Passing this
lane does not change lifecycle, installation eligibility, routing, activation
evidence, or the `no_positive_claim` ceiling.

`tools/validate_all_skills.py` runs official-document bundle discovery and the
tracked-storage audit in report mode. Missing and semantically valid `partial`
bundles, centrally forbidden legacy artifacts, and index/worktree drift are
printed as release blockers without stopping ordinary development validation.
Invalid registries, malformed registrations, missing registered files,
unregistered pack files, unsafe paths, untracked legacy `official-*` files,
storage baseline mismatch, and semantic validation failures still exit
nonzero in report mode.

Supply `--baseline-ref <trusted-base-ref>` for every reviewed change. It makes
pack migration one-way and makes legacy tracked storage delete-only. Updating
candidate counts, digests, or local-control identities cannot hide an
addition, restoration, content/mode rewrite, or artifact/control
reclassification relative to the baseline. Running without a baseline proves
current exactness only. The first reviewed commit that introduces each
migration registry is a bounded bootstrap; after that commit, the Git
baseline is mandatory.

Before tagging, strict validation with a trusted baseline is mandatory. It
exits 3 unless every source-backed Skill has a semantically `complete` bundle at
`skills/<skill-id>/references/official-source-pack/bundle.json`. There is no
grandfather allowlist: migration removes blockers only when real production
packs pass. Strict mode also requires zero release-blocking legacy artifact
paths and an index-equivalent worktree. A complete pack cannot hide tracked
legacy bytes whose central `bundle_content` policy is `forbidden`.

Every pushed tag is treated as a release attempt. Tag CI selects a trusted
event baseline and runs the same strict command once as a post-tag
verification. It does not replace the mandatory fresh pre-tag command or
external tag protection. The current legacy inventory intentionally freezes
release tags until both real pack coverage and tracked-storage migration
close. The discovery record shape and status matrix are
defined in [official-document-bundle-convention.md](official-document-bundle-convention.md).
Passing this gate establishes official-document coverage assurance only; it
does not establish native execution, numerical convergence, physical validity,
or scientific acceptance.

Only after that tag strict gate exits successfully, CI builds the active-only
tar twice, compares the candidates byte-for-byte, verifies both archives from
independent empty extraction directories, and emits the SHA-256 of the selected
candidate. CI uploads that tar and checksum as a GitHub Actions workflow
artifact for review. This is a CI artifact, not a GitHub Release asset: the
repository does not yet publish a Release asset or bind a published Release
asset digest back to the reviewed tag/release record. That release-asset
publication and digest-binding step remains an explicit release-engineering
gap and must not be inferred from a successful tag workflow.

The release build uses `--require-clean-commit`. It rejects ordinary tracked or
untracked changes and also rejects any selected source input that is absent
from the declared commit or whose Git blob bytes or executable bit differ from
that commit. This includes ignored files if they would otherwise enter an
active Skill, contract, or externalization receipt. Omitting the flag remains
available for local candidate-worktree diagnostics, but that output is not a
release artifact even when its two builds happen to compare equal.

When the corresponding tools are implemented, releases must also require:

- privacy and restricted-content validation;
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

The active-only distribution must exclude routable or installable development
Skill metadata, development Skill source trees, private runtime records,
restricted files, raw calculation trees, unpublished results, credentials, and
licensed potential contents. It may carry exact, inert
`registry/source-snapshots/` bytes solely when generated active
official-document packs either depend on or already bind those canonical
registry hashes. Those snapshots are provenance inputs, not the packaged routing registry: the
unpacked verifier must hash them byte-for-byte, must never route or install
from them, and must keep the live authority registry equal to the reverse
closure of active consumer bindings.

Active-only archive verification must independently reject malformed JSON,
missing or unregistered pack records, record-reference hash mismatches,
dangling processor or dependency-lock references, and authority closure that
is broader or narrower than the active bindings. It must replay the portable
official-document contract, content-addressed reference checks, exact active
consumer subset, packaged seed/input bindings, and packaged Skill-source
inventory from the unpacked tree. It must also reproduce every live filtered
registry byte from the inert source snapshots using the canonical build rules,
and reproduce the complete normalized tar byte stream. A member-valid tar with
noncanonical headers, malformed EOF padding, or any bytes after the canonical
EOF is invalid. Legacy official-document bodies whose central storage policy
forbids release remain externalized; their absence caps the portable audit at
`partial` and must not be reported as full source-tree or upstream-content
replay.

The portable audit does not replace the canonical source-repository gates.
Before release, the exact source commit must still pass
`build_official_document_packs.py --all --check` and the full semantic bundle
audit with every non-pack Skill source reference available. A deterministic
archive, an exact source-registry snapshot, or a portable `partial` result does
not by itself establish complete official-document materialization,
redistribution permission, freshness, native execution, numerical
convergence, physical validity, or scientific acceptance.

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
