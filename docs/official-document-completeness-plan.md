# Official-document completeness plan

## Objective

Make official-source coverage for every source-backed Skill explicit,
version-matched, license-aware, reproducible, and machine-verifiable without
equating documentation coverage with parser maturity, native execution,
numerical convergence, physical validity, or scientific acceptance.

This plan does not promote a Skill, enable a route, widen a claim ceiling, or
authorize external execution. Lifecycle changes remain dedicated reviewed
changes under `docs/lifecycle-promotion-policy.md`.

## Live implementation checkpoint — 2026-07-24

The registration layer is now implemented for all 26 source-backed Skills:

- 45 authority records are active and 19 authority records remain planned
  placeholders;
- 57 exact authority-to-consumer bindings close the current consumer graph;
- 26 canonical source-pack directories are present;
- 57 corpus manifests partition 3,421 discovered source identities into 462
  included sources and 2,959 reviewed exclusions;
- Skill lifecycle remains 7 `active`, 19 `development`, and 0 planned Skill
  placeholders.

The packs at this checkpoint are **metadata-only registration packs**. Their
1,586 slices comprise 421 whole-source selectors, 1,159 source-symbol
selectors, and 6 JSON Pointers; none is materialized official-document content
in the canonical pack domain. Their presence establishes a machine-checkable
registration envelope. Fine-grained selector shape alone does not establish
that official document bodies are materialized, that the selected content was
independently replayed, or that the full upstream corpus has been completely
partitioned.

The repository separately retains 2,075 legacy official-document artifacts
totaling 13,412,851 bytes. The storage audit treats them as a distinct domain
outside canonical packs and blocks all of them under strict release. They do
not provide materialized-body or semantic-slice evidence for the packs.

The ordinary bundle audit reports:

| Status | Count |
|---|---:|
| `complete` | 0 |
| `partial` | 26 |
| `missing` | 0 |
| `invalid` | 0 |

The assurance dashboard exposes the stricter layer-by-layer state:

| Layer | `complete` | `partial` | `blocked` | `missing` |
|---|---:|---:|---:|---:|
| Registration | 26 | 0 | 0 | 0 |
| Inventory | 0 | 11 | 15 | 0 |
| Content materialized | 0 | 0 | 16 | 10 |
| Semantic slice | 0 | 1 | 16 | 9 |
| Assurance overall | 0 | 0 | 16 | 10 |

| Dimension | `complete` | `partial` | `blocked` | `missing` | `unknown` |
|---|---:|---:|---:|---:|---:|
| Corpus | 0 | 11 | 15 | 0 | 0 |
| Slice | 0 | 10 | 16 | 0 | 0 |
| Scope | 0 | 5 | 21 | 0 | 0 |
| License | 0 | 26 | 0 | 0 | 0 |
| Storage | 0 | 22 | 4 | 0 | 0 |
| Freshness | 0 | 0 | 0 | 0 | 26 |
| Final overall | 0 | 0 | 25 | 1 | 0 |

The provider layer contains 57 corpus records (`32 partial / 25 blocked`), 57
slice manifests (`29 partial / 28 blocked`), and 57 license reviews (`57
partial / 0 blocked`). Only the canonical CP2K manual corpus passes
`upstream_universe_complete`; no declarative local catalog may self-certify
that upstream-universe state.

Registration `complete` means that the pack is present and its registry,
schema, identity, and binding envelope closes. It is not
`corpus_complete`, `slice_complete`, or
`complete_for_declared_skill_scope`. The ordinary bundle audit consequently
keeps all 26 packs at `partial` while the substantive assurance layers remain
incomplete.

The original baseline conclusions that central authorities, exact consumer
bindings, and canonical pack directories were absent are superseded by this
live graph. Their substantive follow-on questions—upstream inventory closure,
content availability, semantic preservation, and declared-scope coverage—are
not superseded.

Red-team closure now runs the canonical builder check in CI, content-binds any
claim of exact license-terms bytes, scopes blockers by dimension, enforces exact
corpus↔slice and bidirectional loss closure, rejects declarative
self-certification while binding rolling-source aggregates, independently
verifies portable active-only archives, and derives dashboard rows from the
cross-validated registries. These are assurance controls, not document-body
materialization.

## Completion vocabulary

Use the following terms exactly:

- `corpus_complete`: the pinned upstream discovery universe is closed by
  included source records and reviewed exclusions.
- `slice_complete`: every included source has an ordered, reproducible slice
  mapping or a reviewed loss record.
- `complete_for_declared_skill_scope`: every declared capability, task,
  parameter, and documented claim resolves to version-matched slices.
- `partial`: a measured, disclosed gap exists.
- `blocked`: authority, version, license, source identity, or required evidence
  cannot yet support the declared scope.

Do not use `full`, `complete`, or `verified` without naming the applicable
dimension and declared scope.

## Required identity chain

Every documented behavior claim must resolve through this chain:

```text
Skill claim/capability/task/parameter
  -> coverage record
  -> ordered document slice
  -> exact upstream source record
  -> authority + version/tag/commit/revision
  -> raw hash or verified external resolver receipt
  -> license and storage decision
```

An official URL alone does not establish content identity. A local hash alone
does not establish authority, version applicability, redistribution permission,
or corpus completeness.

## Data model

### Authority provider classes and lifecycle

`official-source-authorities.yaml` classifies each authority provider as
`software`, `standard`, `platform`, `repository`, `model-artifact`, `dataset`,
or `publisher`. Only `software` providers are foreign-keyed to active or
planned entries in `software-registry.yaml`; the other classes have independent
namespaces whose closure is established by the authority record and explicit
consumer bindings.

Authority lifecycle describes the review state of the source boundary, not the
lifecycle of software or a Skill. An `active` authority may therefore serve a
planned software entry without promoting, routing, installing, or activating
that software or its intended Skill. Every active software provider must have
at least one active software-class authority. Every planned software provider
must have at least one active or planned software-class authority. Unknown
software-class provider identifiers fail closed.

### Official corpus manifest

The corpus manifest defines one pinned discovery universe. It must record:

- authority and provider identifiers;
- exact version, tag, commit, revision, or reviewed rolling-snapshot identity;
- discovery roots, enumerator identity, retrieval interval, and index hashes;
- every discovered source item;
- included sources and reviewed exclusions;
- per-source raw identity or external resolver identity;
- documentation-specific license decision;
- corpus status and limitations.

For a complete corpus:

```text
discovered = included union reviewed_exclusions
included intersect reviewed_exclusions = empty
```

No count threshold or curated topic list may substitute for exact set closure.

### Document slice manifest

The slice manifest must bind every derived item to exact source bytes or a
verified external source locator. It must record:

- source record and source hash;
- transformer name, version, configuration, and dependency lock;
- ordered slice identifiers, source locators, and slice hashes;
- for external byte-range slices, both the exact whole-source
  `raw_sha256`/`raw_bytes` and selector-bound
  `selected_sha256`/`selected_bytes`;
- a central selection attestation that exactly binds `source_id`, whole-source
  identity, selector, selected hash, and selected length;
- duplicate, overlap, orphan, and ordering checks;
- a loss ledger for links, tables, formulas, code blocks, admonitions, images,
  assets, footnotes, anchors, and other non-text structure;
- transformation and modification notices required by the source license.

Searchable plain text is a derived view. It is not a replacement for structured
or raw source identity when the transformation loses semantics.

### Skill document coverage

Coverage is many-to-many. One canonical provider source pack may be consumed by
multiple Skills, and one Skill may consume multiple software, standard,
library, scheduler, or official-repository authorities.

Coverage must be queryable by at least:

```text
Skill x provider x version x executable x capability x task
      x parameter x observable x backend x documented claim
```

Unsupported or unautomated surfaces remain classified and discoverable; they
must not disappear from the reverse coverage check.

### License and storage decision

Every tracked official artifact must resolve to a reviewed decision covering:

- source owner and documentation-specific license or terms;
- raw, derived text, metadata, image, PDF, model, potential, and example-data
  storage classes as applicable;
- attribution, notice, share-alike, modification, and redistribution duties;
- reviewed storage mode: `embedded-open`, `external-cache`,
  `metadata-only`, `external-runtime-only`, or `excluded`;
- review date, evidence URLs, limitations, and supersession state.

Unknown or restricted content defaults to metadata plus an external resolver.
Licensed potentials, credentials, private artifacts, and restricted manuals
never enter Git.

## Implementation waves

### Wave 0: contracts and enforcement

1. Add strict corpus, slice, coverage, and license-review contracts.
2. Add deterministic offline validators and exact-set negative tests.
3. Separate Skill lifecycle from official-source verification lifecycle.
4. Permit many-to-many authority consumers without widening provider authority.
5. Require stronger claim profiles to inherit weaker official-source gates.
6. Add a maintenance-only CI lane for every source-backed development Skill.
7. Add a repository audit that rejects tracked content forbidden by its
   registered storage decision.

Acceptance:

- malformed, incomplete, duplicate, overlapping, orphaned, version-mismatched,
  unlicensed, and unbound records fail closed;
- development tests run without making development Skills routable;
- no active or development lifecycle changes occur.

Wave 0 enforcement uses two independent domains:

- canonical `references/official-source-pack/**` records are closed by bundle
  registration and the five semantic contracts;
- legacy tracked `official-*` mirrors and controls are closed by
  `registry/official-document-storage-discovery.yaml`.

The exact canonical pack path is excluded from legacy storage discovery; no
near-match is excluded. Candidate worktree bytes are audited without requiring
staging, while index/worktree drift remains visible and blocks strict release.
After the one-time registry bootstrap, Git baseline comparison permits only
legacy artifact deletion. Additions, restorations, byte/mode rewrites,
artifact/control reclassification, and local-control changes fail even when a
candidate updates its own counts or digests.

At the 2026-07-24 checkpoint, this legacy domain contains 2,075 artifacts
(13,412,851 bytes); all 2,075 are strict-storage release blockers. These bytes
remain outside the 26 canonical pack directories.

### Wave 1: active correctness blockers

Add minimal negative fixtures before fixing:

- QE truncated official-reference retrieval and non-executable action templates;
- VASP per-step electronic convergence, completion, version, unknown-tag, and
  input-set identity false passes;
- CP2K forged live-source evidence and missing base-topic inheritance;
- SIESTA wildcard, SOC-pseudopotential, XC identity, planned-observable, and
  supplement-provenance false passes;
- postprocessing backend-level maturity and self-declared maturity.

Acceptance:

- every reproduced false pass becomes a stable failing fixture before the fix;
- the fixture passes only after the root cause is fixed;
- existing claim ceilings do not increase.

### Wave 2: active official-source packs

All seven active source-backed Skills now have metadata-only registration packs.
The following items remain content and semantic-coverage targets; pack presence
does not close them:

- QE: enumerate the pinned release tree, top-level and package `Doc/`/`doc/`
  roots, documentation-bearing source headers, version archives, broken links,
  and every bundled or linked third-party exception; do not treat current web
  `Doc/` hashes as exact-release tree closure.
- VASP: resolve the Wiki licensing decision before expanding storage; split
  `core`, `reference-categories`, and a precisely defined comprehensive scope;
  bind page revisions, aliases, changelog, and known issues.
- CP2K: bind a release commit, generated input XML, generator, prose sources,
  full page inventory, complete section/keyword anchors, and explicit
  documentation-scope license evidence; the repository GPL file alone does not
  establish documentation-scope clearance for `docs/**` body materialization.
- SIESTA: separate release-code, documentation-portal, and source-supplement
  authorities; treat the 47 release manual TeX files as documentation-scope
  unproven, limit the GPL-header candidate set to the six explicitly reviewed
  source supplements, and pin portal-source investigation to the `5.4` commit
  `6c58d08b6aef7f1c8d20d85c215e96ce98e47870` rather than using `master` as
  proof of the rendered body.
- CIF, postprocessing, and campaign efficiency: bind standards, formats,
  libraries, backends, and software-behavior claims to canonical source packs.

Acceptance:

- corpus, slice, and declared-scope status are reported separately;
- any exclusion has a reviewed reason;
- documentation completeness never promotes parser or scientific maturity.

### Wave 3: development source packs

All 19 development Skills now have metadata-only registration packs and remain
non-routable and non-installable. Continue without promotion:

1. open, exact-source providers: LAMMPS, Phonopy, GROMACS, GPUMD;
2. multi-component providers: CatMAP, DeePMD/dpdata/DP-GEN, ASE/pymatgen/RDKit;
3. license/version-complex providers: Multiwfn, VASPKIT, OVITO;
4. aggregate ML providers: MACE, NequIP, FairChem generations, and model cards;
5. restricted providers: Gaussian, LOBSTER, and LASP through external
   hash-and-locator resolvers only.

Cross-cutting reporting, literature, and review Skills consume canonical source
records; they do not duplicate upstream manuals.

## Remaining closure work

The next work must improve substantive assurance without relabeling registration
as document completeness.

### 1. Materialize permitted content

For every redistributable source, bind the pack to exact retrieved bytes,
length, hash, version, and storage decision. For restricted sources, retain
metadata-only or external-runtime-only storage and disclose the resulting
coverage blocker. A whole-source receipt is useful identity evidence but is not
the document body. The repository root currently has no `LICENSE`; before
adding any third-party body, a reviewed root license/notice policy or explicit
third-party-content isolation policy is a governance prerequisite, not a legal
conclusion about the upstream source.

Implement body storage first through a minimal
`materialized-open-content-v1` adapter. It must consume exact authority,
version/source-root and raw-byte identities, a closed corpus/exception
partition, documentation-specific terms/reviewer attestation, an explicitly
permitted storage mode, notices, and a deterministic selector/transformer
lock. It must emit immutable raw bytes plus content-bound slices, exact
source→slice mappings, selected hashes/lengths, notices, transformations, and a
closed loss ledger. Acceptance requires byte-identical clean runs, confined
paths, rehashing of every stored byte, exact corpus/slice/exception closure,
and fail-before-mutation behavior for wrong revisions, changed bytes, missing
notices, unknown documentation scope, unlisted third-party content, or absent
license authority. The resulting bundle must pass strict storage, portable
active-only, and full repository audits without changing lifecycle or
scientific claim ceilings.

### 2. Materialize and strengthen selector-bound slices

Replace the 421 whole-source selectors with deterministic, source-specific
heading, section, source-symbol, page-range, line-range, byte-range, or JSON
Pointer selectors where the source format permits them. Bind the existing
1,159 source-symbol and 6 JSON Pointer selectors to materialized or equivalently
attested content before treating them as semantic slices. Record transformer
and dependency identity, stable ordering, duplicate/overlap/orphan checks, and
reviewed losses for links, tables, formulas, code, images, anchors, and other
structure. Selector shape alone must not raise semantic-slice assurance.

### 3. Attest the reviewed license-terms bytes

Bind each documentation-specific license/storage review to the exact terms
bytes or a content-addressed equivalent, not only to an arbitrary HTTPS
locator. Cover every relevant material class separately; a software license
does not automatically license documentation, images, examples, model weights,
datasets, or derived text. The validator now prevents registry bytes from
masquerading as exact terms content, but all 57 current license reviews remain
honestly `partial` until authoritative terms/reviewer attestation exists.

### 4. Require resolver receipts and platform attestation

An external resolver receipt must bind resolver implementation, platform,
authority, locator, requested and resolved version, observed raw hash and
length, selection identity, and retrieval time. Self-declared or
unattested receipts remain insufficient for a complete source-identity or
content-materialization claim.

### 5. Keep freshness independent

Use scheduled live discovery to report changed tags, revisions, locators,
ETags, Last-Modified values, inventory membership, and observed hashes. Do not
silently mutate pinned identities. Offline pack integrity and current upstream
freshness remain separate statuses, and a stale or unobserved source cannot be
upgraded by a passing offline build.

The dashboard derives its exact row set from the cross-validated source-backed
Skill registry and official-document expectation registry; it does not carry a
second numeric Skill-count constant. Its offline freshness baseline remains
`unknown`. A freshness overlay may replace that baseline with `complete` only
when it covers the row's exact corpus-authority set, every authority is
reported complete, the explicit dashboard as-of time falls inside the
observation validity interval, and the overlay is platform-attested with a
trust identifier. Partial, expired, future, or unverified overlays leave the
row `unknown`; any reported authority blocker conservatively caps the row at
`blocked`.

The immediate unresolved evidence is bounded: subject→slice mapper attestation;
independent inventory wiring for the 15 inventory-blocked Skill rows;
materialized source adapters plus authoritative license attestation; and a
fresh live drift observation. The current drift report attempted 52 checks and
reported all 52 as `unavailable`, not unchanged.

## CI lanes

### Pull-request offline lane

- schema and semantic validation;
- exact corpus/slice/coverage/license closure;
- active and development deterministic tests and compile checks;
- mutation tests for missing pages, duplicate slices, broken anchors, mixed
  versions, forbidden tracked bytes, and unbound claims;
- Git-baseline mutation tests for pack downgrade/deletion, legacy-artifact
  addition or rewrite, and local-control reclassification;
- deterministic four-layer registration, inventory, content-materialization,
  and semantic-slice dashboard generation;
- active-only artifact construction and unpacked verification against exact
  bundle expectations.

### Scheduled live lane

- upstream discovery and revision drift;
- freshness service-level status;
- tag, commit, revid, ETag, Last-Modified, and observed hash changes;
- machine-readable reports only; updates enter the repository through review.

Local integrity and upstream freshness must always be reported separately.

## Release blockers

A release is blocked when:

- a tracked official artifact lacks a license/storage decision;
- a registered `bundle_content: forbidden` authority contributes release bytes;
- a complete status lacks exact discovery closure;
- a metadata-only or whole-source-only pack overclaims content materialization
  or fine-grained semantic slicing;
- a documented claim lacks a version-matched source/slice binding;
- a stronger claim profile drops a required official-source gate;
- a development source tree is omitted from maintenance validation;
- a known false-pass fixture regresses;
- an activation record, coverage record, or source identity is invalid.

## Verification

Every completed implementation wave must run:

```text
python3 tools/run_tests.py
python3 tools/run_development_tests.py
python3 tools/build_official_document_packs.py --all --check
python3 tools/validate_all_skills.py --baseline-ref <trusted-base-ref>
python3 tools/audit_repository.py
git diff --check -- . ':(exclude)skills/qe-rigorous-calculations/references/official-*'
```

`validate_all_skills.py` now discovers official-document registration packs
and audits legacy tracked storage in report mode. Release-tag CI runs one
`--strict-release` invocation with a trusted baseline: every missing or
valid-but-partial pack and every centrally forbidden tracked artifact remains
a release blocker. The current registration migration has removed `missing` and
`invalid` bundle results, but all 26 ordinary bundle results remain `partial`;
materialization, fine-grained slicing, attestation, and freshness gaps therefore
remain visible rather than grandfathered. Legacy artifacts are removed
monotonically; there is no grandfather allowlist and no synthetic fixture may
stand in for a production pack. Passing these commands proves only the scopes
they actually validate.
