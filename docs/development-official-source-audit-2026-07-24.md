# Development Skill official-source audit — 2026-07-24

## Live result

The repository now has a closed registration graph for all 26 source-backed
Skills:

- 45 active authority records and 19 planned authority placeholders;
- 57 exact authority-to-consumer bindings;
- 26 canonical source-pack directories, one for each of the 7 active and 19
  development source-backed Skills;
- 57 corpus manifests covering 3,421 discovered source identities, partitioned
  exactly into 462 included sources and 2,959 reviewed exclusions;
- Skill lifecycle remains 7 `active`, 19 `development`, and 0 planned Skill
  placeholders.

This is registration closure, not official-document completeness. All 1,586
generated slices are metadata-only artifacts: 421 use whole-source selectors,
1,159 use source-symbol selectors, and 6 use JSON Pointers. None is
materialized official-document content in the canonical pack domain. These
**metadata-only registration packs**
prove that the registered Skill, provider, version scope, source identity,
license/storage decision, and coverage envelope can be checked together. Even
the 1,165 fine-grained selectors bind external metadata identities rather than
repository content, so they do not prove that official document bodies have
been embedded or otherwise fully materialized, or that the full upstream
corpus has been semantically partitioned.

The repository separately retains 2,075 legacy official-document artifacts
totaling 13,412,851 bytes. They are outside the canonical pack domain and all
are strict-storage release blockers. Their presence does not convert canonical
metadata records into materialized pack content or prove semantic slicing.

No Skill was promoted, made installable, made routable, or granted a higher
scientific claim ceiling by this work.

## Live audit layers

The ordinary bundle audit reports:

| Status | Count |
|---|---:|
| `complete` | 0 |
| `partial` | 26 |
| `missing` | 0 |
| `invalid` | 0 |

The four-layer dashboard intentionally separates registration from document
substance:

| Layer | `complete` | `partial` | `blocked` | `missing` |
|---|---:|---:|---:|---:|
| Registration | 26 | 0 | 0 | 0 |
| Inventory | 0 | 11 | 15 | 0 |
| Content materialized | 0 | 0 | 16 | 10 |
| Semantic slice | 0 | 1 | 16 | 9 |
| Assurance overall | 0 | 0 | 16 | 10 |

The independent dashboard dimensions are:

| Dimension | `complete` | `partial` | `blocked` | `missing` | `unknown` |
|---|---:|---:|---:|---:|---:|
| Corpus | 0 | 11 | 15 | 0 | 0 |
| Slice | 0 | 10 | 16 | 0 | 0 |
| Scope | 0 | 5 | 21 | 0 | 0 |
| License | 0 | 26 | 0 | 0 | 0 |
| Storage | 0 | 22 | 4 | 0 | 0 |
| Freshness | 0 | 0 | 0 | 0 | 26 |
| Final overall | 0 | 0 | 25 | 1 | 0 |

At provider-record granularity, 57 corpus records are `32 partial / 25
blocked`, 57 slice manifests are `29 partial / 28 blocked`, and all 57 license
reviews are `partial` with zero blockers. Exactly one corpus, the canonical
CP2K manual corpus, passes `upstream_universe_complete`. License review remains
partial because an unattested locator or unverified reviewer authority cannot
support complete assurance, even though unrelated content blockers no longer
pollute the license dimension. Freshness remains `unknown` for every Skill.

The bundle audit's 26 `partial` results and the dashboard's 26 registration
`complete` results answer different questions. The former conservatively caps
the whole bundle while any substantive layer remains incomplete. The latter
means only that the registration object exists and closes its schema and
binding checks. Neither result authorizes the phrase “official documents are
fully split into Skills.”

## Superseded baseline findings

The initial audit reported missing central authority entries, missing
authority-to-consumer bindings, and missing canonical pack directories. Those
findings have been superseded by the live graph above:

- the central authority registry now contains 45 active authorities and 19
  planned authority placeholders;
- the consumer registry now contains 57 exact bindings;
- all 26 source-backed Skills now have canonical metadata-only registration
  packs, so bundle `missing` and `invalid` are both zero.

The supersession is deliberately narrow. A central authority record or exact
binding is not an assertion that upstream bytes were retrieved, that the
upstream documentation universe was completely discovered, or that the
resulting content was semantically partitioned.

## Red-team controls closed

The implementation now:

- runs `tools/build_official_document_packs.py --all --check` from the
  repository validation and CI path before bundle assurance is reported;
- rejects a registry hash, registry bytes, or central trust assertion that
  masquerades as exact license-terms content;
- projects runtime, body, license, inventory, and scope blockers only to their
  applicable dimensions;
- requires one exact slice manifest per corpus, exact source partitioning, and
  bidirectional slice/loss-ledger closure;
- rejects declarative inventory self-certification and binds rolling-source
  identity to the aggregate of every raw source identity;
- verifies active-only archives using their portable registry snapshot and
  exact packaged pack closure; and
- derives dashboard rows from the cross-validated Skill and bundle-expectation
  registries rather than a second hard-coded count.

These controls remove false-positive assurance paths. They do not materialize
official bodies or attest every upstream inventory.

## Remaining blockers

### Content materialization

All canonical pack slices retain metadata rather than repository-stored
official document bodies. For restricted or externally resolved sources this
may be the correct storage policy; for redistributable sources, a reviewed
embedded or content-addressed materialization route is still needed. A URL,
revision string, or hash-shaped field is not evidence that the bytes were
actually available to the build. The separate legacy-storage domain does not
satisfy this pack-level requirement.

### Fine-grained semantic slicing

The 421 whole-source receipts preserve source identity but do not provide
fine-grained mappings for the Skill's claims. The 1,165 source-symbol and JSON
Pointer selectors are more specific, but currently select external metadata
identities rather than materialized bytes. Each provider still needs a
deterministic source-specific transformer, ordered slice identities,
overlap/orphan checks, a loss ledger for tables, formulas, links, code, images,
anchors, and other structure, and an independently trusted subject→slice
mapper attestation.

### Inventory, materialization, and license authority

Fifteen Skill rows remain inventory-blocked pending independent upstream
inventory wiring. Only the canonical CP2K manual corpus currently proves
`upstream_universe_complete`; a declarative local catalog cannot appoint itself
as that proof. Materialized adapters must bind permitted body bytes to exact
source and selector identities, while authoritative license review must bind
the exact reviewed terms, reviewer authority, and material-class decision.
Current license rows honestly remain partial rather than blocked.

### Resolver receipt and platform attestation

External and restricted sources need receipts that bind resolver identity,
source locator, selected version, observed raw hash and length, retrieval time,
and platform attestation. A self-declared receipt must not be sufficient to
upgrade source identity or coverage to complete.

### Freshness

Offline registration integrity and live upstream freshness remain separate.
Rolling documentation, changed tags or revisions, redirected locators, ETags,
Last-Modified values, and observed hashes need scheduled drift checks. Drift
reports must enter review rather than silently rewriting trusted source
identity. The current live report contains 52 checks and all 52 are
`unavailable`; this is missing observation evidence, not evidence of no drift.

## Development-pack migration order

Continue without lifecycle promotion:

1. Materialize and semantically slice open, exact-source providers such as
   LAMMPS, Phonopy, GROMACS, and GPUMD.
2. Keep multi-component providers separate: CatMAP; DeePMD-kit, dpdata, and
   DP-GEN; ASE, pymatgen, spglib, and RDKit.
3. Preserve distinct license and execution surfaces for Multiwfn, VASPKIT, and
   OVITO.
4. Keep MACE, NequIP, FairChem package generations, model cards, weights, and
   datasets as separately identified and licensed artifacts.
5. Keep Gaussian, LOBSTER, and LASP restricted manuals external and `blocked`
   until an authorized, attestable resolver can provide the required evidence.
6. Let reporting, literature, and review Skills consume canonical upstream
   records rather than duplicating manuals or inventing a finite “all
   literature” corpus.

## Acceptance boundary

Future progress must be reported independently for:

```text
registration
  -> upstream inventory closure
  -> exact content materialization
  -> fine-grained semantic slicing
  -> declared Skill-scope coverage
```

A later layer cannot be inferred from an earlier one. In particular, 26 present
and schema-valid packs, 45 active authorities, 57 exact bindings, or passing
offline tests do not establish corpus completeness, native execution,
calculation correctness, numerical convergence, physical validity, or
scientific acceptance.
