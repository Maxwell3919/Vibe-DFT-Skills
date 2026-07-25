# Official-document storage audit — 2026-07-24

## Scope and status

This audit records the Git-index footprint and policy alignment of the four
active calculation Skills. It is a storage and provenance audit, not legal
advice. It does not authorize redistribution, remove existing files, rewrite
Git history, promote a Skill, widen a route, or establish scientific validity.

The historical baseline table is derived from tracked Git blobs. The enforced
candidate view additionally reads regular worktree bytes for every tracked
namespace path and scans for untracked namespace files, so local validation
does not require staging and cannot silently ignore unstaged changes. It
excludes filesystem allocation overhead and runtime data.

## Repository-wide result

| Provider | Tracked blobs | Tracked bytes | Current central bundle policy | Audit result |
|---|---:|---:|---|---|
| Quantum ESPRESSO | 1,819 | 8,676,290 | `forbidden` | conflict |
| VASP Wiki | 164 | 1,737,986 | `forbidden` | conflict |
| CP2K | 89 | 2,716,151 | `forbidden` | identity pin retained; redistribution blocked |
| SIESTA | 3 | 282,616 | `forbidden` | authority and provenance conflict |
| **Total** | **2,075** | **13,413,043** | — | — |

This table is the pre-candidate Git-index baseline. All 2,075 audited blobs
totaling 13,413,043 bytes were tracked while their current central authorities
forbid bundled content. CP2K retains a canonical snapshot as an identity
boundary, but that pin no longer doubles as redistribution authorization.
Passing a Skill-local mirror check does not resolve a central policy
contradiction.

## Enforced candidate inventory

`registry/official-document-storage-discovery.yaml` and
`tools/validate_official_document_storage.py` now close the candidate
worktree/index boundary:

| Artifact set | Paths | Candidate bytes | Authority evaluation | State |
|---|---:|---:|---|---|
| `qe-legacy` | 1,819 | 8,676,290 | QE website + QE release source, all-of | blocked |
| `vasp-wiki` | 164 | 1,737,986 | VASP Wiki | blocked |
| `cp2k-manual` | 88 | 2,706,893 | CP2K manual | blocked |
| `cp2k-source-registry` | 1 | 9,258 | CP2K manual + release source, all-of | blocked |
| `siesta-portal-registry` | 1 | 2,594 | SIESTA portal | blocked |
| `siesta-release-derived` | 2 | 279,830 | SIESTA release source | blocked |
| **Content artifact total** | **2,075** | **13,412,851** | — | **blocked** |

The VASP total includes `official-wiki-index.md` as derived official content,
not as a local control. Four additional exact local controls are classified
separately:

| Local control | Candidate bytes |
|---|---:|
| CP2K `official-source-policy.md` | 4,399 |
| SIESTA `official-artifact-fixtures.json` | 2,006 |
| SIESTA `official-artifact-forward-tests.md` | 1,411 |
| SIESTA `official-sources.md` | 3,886 |
| **Control total** | **11,702** |

The resulting namespace is therefore exactly 2,079 files: 2,075 official
content artifacts plus four local controls. The aggregate candidate control
identity is
`480086ef3c1f9ab255717e38e2404fa5ae5cfee5fed24f27dd8ad0eecf8cf53b`.
Every control also has an exact mode, byte count, and Git-blob identity; it
cannot become a payload escape lane.

The candidate differs from the pre-candidate index at three explicit paths:

- CP2K `official-source-policy.md`;
- SIESTA `official-source-supplements.json`;
- SIESTA `official-sources.md`.

Normal audit reports those three worktree/index drifts and exits 0 because the
candidate baselines match the worktree. Strict release exits 3 and requires an
index-equivalent worktree. On the first reviewed storage-registry commit,
current exactness establishes the bootstrap. Every later change compares
against a real Git commit: legacy artifacts may only be deleted, while
addition, restoration, content/mode rewrite, control change, or
artifact/control reclassification is invalid even if candidate digests are
updated.

The exact canonical pack domain
`skills/<skill-id>/references/official-source-pack/**` is intentionally
excluded from this legacy namespace. It is governed independently by exact
pack registration, corpus/slice/license/scope/coverage contracts, and semantic
validation. `official-source-pack-copy/` and every other near-match remain in
the closed legacy namespace.

No tracked POTCAR, UPF, PSF, VPS, PSML, PSP, or equivalent potential payload
was found by the bounded filename audit. Documentation about a potential is
not the potential payload itself.

## Quantum ESPRESSO

### Stored material

| Material | Files | Bytes |
|---|---:|---:|
| Raw input references | 37 | 915,200 |
| Raw HTML user guides | 95 | 475,404 |
| Raw release notes | 1 | 114,203 |
| Raw PDFs | 11 | 3,828,515 |
| Raw discovery indexes | 2 | 23,093 |
| Derived input slices | 1,231 | 1,470,854 |
| Derived guide slices | 95 | 299,308 |
| Derived PDF page text | 171 | 514,575 |
| Derived release-note slices | 121 | 181,404 |
| Derived indexes and metadata | 55 | 853,734 |

### Blocking findings

- The central authority recognizes exact QE 7.5, has no canonical snapshot,
  records licensing as unresolved, and forbids bundled content.
- The local corpus is version-mixed: most input references are 7.5, at least
  `INPUT_LD1` is 7.4, guide families include 7.4 and 7.5, PDFs include multiple
  or unstated versions, and release notes intentionally span historical
  releases.
- A single QE-level license statement cannot cover every attachment. The PDF
  set includes third-party or separately authored material such as the PLUMED
  quick reference and must be reviewed item by item.
- Raw bytes, rendered pages, derived text, PDF assets, and historical release
  records currently share one effective mirror without per-family storage
  decisions.

### Required migration

Split the current material into at least:

1. exact release-source documentation corpora;
2. versioned website-rendered guide corpora;
3. historical release-note corpus;
4. one reviewed record per PDF or homogeneous PDF family;
5. third-party attachment corpora with independent authority and license
   evidence.

Until those partitions close, corpus, slice, license, and declared-Skill-scope
status must be reported separately and cannot exceed `partial` or `blocked`.

## VASP Wiki

### Stored material

| Material | Files | Bytes |
|---|---:|---:|
| Raw MediaWiki JSON with wikitext and expanded HTML | 81 | 1,354,318 |
| Derived Markdown pages | 81 | 338,557 |
| Index and manifest | 2 | 45,111 |

The existing snapshot is a curated `core` of 81 pages, not a complete Wiki
discovery universe. It contains no Wiki image binaries and no VASP source,
binary, or POTCAR payload.

### Blocking findings

- The central authority treats the general website terms as restrictive and
  forbids bundled content.
- Current Wiki pages state that page content is available under GNU Free
  Documentation License 1.2 unless otherwise noted. That page-level statement
  and the general website terms must be reviewed together rather than allowing
  either one to silently override the other.
- Wikitext, expanded HTML/templates, derived Markdown, images/media, Portal and
  forum content, proprietary VASP software, and POTCAR data are distinct
  material classes.
- The local raw JSON and Markdown do not yet close attribution, page history,
  license-copy, modification notice, or per-page exception obligations.
- Category discovery is absent, so `core` cannot be relabeled as a
  corpus-complete Wiki mirror.

### Required migration

Keep separate authorities and storage decisions for Wiki text, Wiki
assets/media, Portal/tutorial/forum content, VASP software, and restricted
potential data. If Wiki-text redistribution is reviewed as permitted, retain
one canonical revision/history-bearing representation and derive searchable
slices reproducibly from it; do not infer permission for assets or proprietary
runtime material.

## CP2K

### Stored material

| Material | Files | Bytes |
|---|---:|---:|
| Curated derived manual pages | 86 | 2,461,214 |
| Full page inventory | 1 | 203,919 |
| Manifest | 1 | 41,760 |
| Source registry | 1 | 9,258 |

The inventory enumerates 2,946 pages while only 86 derived pages are mirrored.
This is a full locator inventory plus a curated content surface, not a complete
manual text mirror.

### Remaining findings

- The central canonical manifest hash matches the tracked manifest and remains
  useful for exact content identity.
- The central storage policy is now `forbidden`: identity pinning is explicitly
  separated from redistribution permission.
- The current license evidence points to the moving `master` branch rather
  than the exact CP2K 2026.2 tag and source commit.
- The source-to-generated-manual chain, documentation-specific license
  applicability, third-party exceptions, attribution, modification notice,
  and repository notice files are not yet closed.
- Complete page discovery does not imply complete page slicing or complete
  Skill coverage.

CP2K is the first migration candidate because it already has an exact manual
version, complete page inventory, content hashes, and a canonical snapshot
boundary.

## SIESTA

### Stored material

| Material | Files | Bytes |
|---|---:|---:|
| Derived FDF source index | 1 | 275,702 |
| Topic source registry | 1 | 2,594 |
| Source supplements | 1 | 4,128 |

### Blocking findings

- The central authority covers the versioned documentation portal under
  CC-BY-NC-SA-4.0 and forbids bundled content.
- The FDF index and supplements are instead derived from the exact SIESTA 5.4.2
  release repository, including `Docs/tex` and selected `Src` records.
- Release-source documentation and source supplements therefore require an
  exact release-source authority and license review distinct from the
  documentation portal.
- Utility manuals/assets and pseudopotential runtime material require their own
  lanes; actual pseudopotential content remains `external-runtime-only` and
  `excluded` from Git.

At minimum, migrate to separate release-source, documentation-portal,
utility/manual-asset, and pseudopotential-runtime authorities.

## Required storage vocabulary

Every source material class must resolve to one reviewed mode:

- `embedded-open`
- `external-cache`
- `metadata-only`
- `external-runtime-only`
- `excluded`

Unknown or unresolved licensing defaults to metadata-only in Git. Binary
assets default to an external content-addressed cache until separately
reviewed. Restricted potentials, licensed binaries, credentials, private
artifacts, and unpublished runtime data are always `excluded` from the
documentation bundle; when a licensed workflow needs them, only an
`external-runtime-only` locator may be recorded. `excluded` is a policy
disposition, not a valid storage mode for an actual slice.

Derived content cannot have a more permissive storage decision than its source.
A generic `other` class must never authorize restricted runtime content.

## Release blockers

Block release packaging when any of the following is true:

- tracked official content contradicts its registered bundle policy;
- a corpus mixes source provenance, version identity, or license rules without
  explicit per-source partitioning;
- an embedded artifact lacks a material-class-specific storage rule;
- a canonical source or derived slice hash is not recomputed from exact bytes;
- a license review relies on a moving branch where an exact release exists;
- required attribution, license copy, history link, modification notice,
  share-alike, source-offer, or third-party notice is missing;
- a license decision is expired, superseded, or unresolved;
- a restricted potential, licensed binary, credential, private artifact, or
  runtime calculation payload enters the documentation bundle.

## Non-destructive migration order

1. Freeze unreviewed documentation refresh and release packaging.
2. Preserve the exact artifact and local-control inventory as the bootstrap
   baseline.
3. Add authority-aware corpus, slice, license, and Skill-coverage contracts.
4. Close CP2K exact-version license and generation provenance first.
5. Split QE by release/version/source family and review PDFs individually.
6. Split VASP Wiki text from assets, Portal content, software, and potentials.
7. Split SIESTA release source from the documentation portal and runtime data.
8. Add repository-level third-party notices and a user-approved repository
   license decision.
9. Move only unresolved or restricted content to `external-cache` after an
   explicit, separately reviewed migration decision.
10. Keep strict release-tag CI enabled during migration. Every missing,
    partial, or invalid production pack remains release-blocking until it is
    migrated; do not hide conflicts behind a grandfather allowlist or
    synthetic complete fixture.

Deleting current files would not remove historical blobs. Any history rewrite
is a separate destructive operation and requires explicit user authorization.

## Reproduction commands

Inspect historical Git-index identities rather than filesystem allocation
sizes:

```bash
git ls-files -s <PATHS...> |
while read -r mode oid stage path; do
  printf '%s\t%s\n' "$path" "$(git cat-file -s "$oid")"
done
```

Check for potential-like tracked payload names:

```bash
git ls-files |
rg -i '(^|/)(POTCAR|POTCAR\.|.*\.(upf|psp8?|psf|vps|psml|gth|pot))$'
```

The 2026-07-24 bounded check returned no matches.

Run the enforced candidate, strict-release, and migration views with:

```text
python3 tools/validate_official_document_storage.py
python3 tools/validate_official_document_storage.py --strict-release
python3 tools/validate_official_document_storage.py --baseline-ref <trusted-base-ref>
```

Without `--baseline-ref`, the tool proves only current candidate exactness.
It does not prove monotonic migration history.
