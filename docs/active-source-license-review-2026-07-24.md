# Active official-source license review — 2026-07-24

## Purpose

This record captures engineering evidence for fail-closed storage decisions.
It is not legal advice, does not choose the repository's own license, and does
not authorize a lifecycle, routing, execution, or scientific claim change.

Evidence was retrieved between `2026-07-23T17:31Z` and
`2026-07-23T17:39Z`. Dynamic terms must be rechecked when their content hash
changes.

## Decision summary

| Source universe | Evidence-based classification | Current Git decision |
|---|---|---|
| QE 7.5 release material | GPL-2.0-or-later evidence exists for the exact release distribution; documentation roots and third-party exceptions remain per-item questions | metadata-only until the exact release-tree roots, notices, and every third-party exception are closed |
| VASP Wiki text | GFDL-1.2-only, separate from proprietary VASP software | existing text is release-blocked until per-page license/history/author obligations close |
| CP2K 2026.2 source-tree docs | the repository GPL file does not establish the license scope of `docs/**` | source and rendered manual remain metadata-only pending explicit documentation-scope and build-provenance evidence |
| SIESTA 5.4.2 release manual/source | the 47 manual TeX files lack established documentation-license scope; six explicitly GPL-headered source supplements are bounded candidates only | keep all body content metadata-only until the two classes receive separate authority and storage decisions |
| SIESTA rendered documentation portal | the exact `siesta-docs` license file and the pinned 5.4 source commit are evidence inputs, not proof of the rendered body or its build lineage | keep the portal body metadata-only pending exact source/build/license-scope closure |

## Repository-level governance blocker

The repository root currently has no `LICENSE`. That absence is not a legal
conclusion about any upstream project, but it prevents a clear repository-level
distribution boundary for newly embedded third-party documentation. Before any
official body text is introduced, maintainers must adopt a reviewed root
license/notice policy or an equally explicit third-party-content isolation and
distribution policy. Until then, the repository-level decision remains
metadata-only even when an upstream artifact may have open terms.

## Quantum ESPRESSO 7.5

### Exact identity

- tag: `qe-7.5`
- annotated tag object: `17975e6f2ba19aec6f50d99c1fc677361d7c8b3a`
- peeled commit: `770a0b2d12928a67048e2f3da8d10d057e52179e`

### Official evidence

| Artifact | Official locator | SHA-256 |
|---|---|---|
| QE 7.5 `License` | `https://gitlab.com/QEF/q-e/-/raw/770a0b2d12928a67048e2f3da8d10d057e52179e/License` | `204d8eff92f95aac4df6c8122bc1505f468f3a901e5a4cc08940e0ede1938994` |
| QE 7.5 `README.md` | `https://gitlab.com/QEF/q-e/-/raw/770a0b2d12928a67048e2f3da8d10d057e52179e/README.md` | `87299e2ae62a98b738a9b9fa05aa436d67cb31d5ef8dffeb7f393f89344b8932` |
| Web user-guide terms | `https://www.quantum-espresso.org/Doc/user_guide/node6.html` | `6cde6126878e19eb028a034a84bbc2f470a4aeb6fd5f9690d20524880033f59a` |
| Current web `INPUT_PW.txt` | `https://www.quantum-espresso.org/Doc/INPUT_PW.txt` | `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d` |

The exact release README states that material in the distribution is under GPL
v2 or later. This is evidence for evaluating exact-release documentation roots,
not a blanket legal conclusion. It does not automatically assign QE 7.5
identity or one license decision to unversioned web renders, older manuals, or
third-party attachments.

The release inventory must enumerate exact documentation roots in the peeled
commit, including the top-level `Doc/`, package-local `Doc/` or `doc/`
directories, and documentation-bearing source headers selected for coverage.
Each bundled or linked third-party file, image, attachment, generated asset, or
separately licensed component is an exception until its own origin, terms,
notice, and redistribution decision close. The current web `Doc/` hashes above
do not substitute for that exact-release tree inventory.

### Review gates and limits

- determine and record the applicable license and copyright notices;
- review whether a modifiable source form must accompany derived documentation;
- record transformations or modifications and their date;
- obtain an authoritative decision for the terms applicable to derived text;
- keep scientific citation requests separate from redistribution obligations;
- split every older, unversioned, or third-party attachment into its own
  version/license decision.

Current status: `blocked-until-notice-and-corpus-partition-close`.

## VASP Wiki

### Official evidence

| Artifact | Official locator | SHA-256 |
|---|---|---|
| MediaWiki rights information | `https://www.vasp.at/wiki/api.php?action=query&meta=siteinfo&siprop=rightsinfo&format=json&formatversion=2` | `da9c93116168d5f82463201c447041714465bd66c2034f4eb6ab1cbf970cf971` |
| GNU FDL 1.2 text | `https://www.gnu.org/licenses/old-licenses/fdl-1.2.txt` | `2652c22ba086f92e55ae4a9f9c890ad4766ffd7814a73d318e22a597edf857a4` |
| VASP website terms | `https://www.vasp.at/footer/termsofuse/` | `ef5a79716c8422e542f6c21d16572bb8ef0da1bf1caf339a4c4e2e585ee558d3` |
| VASP proprietary-software statement | `https://vasp.at/info/faq/public_domain/` | `3112387feaaa8450f73ae9b8892803c4a1b0a292acd0148397d06df63558efb0` |

The MediaWiki site information identifies Wiki content as GNU Free
Documentation License 1.2. This Wiki license does not license VASP source,
binaries, Portal downloads, or POTCAR data.

### Required obligations and limits

A release pipeline for modified Markdown must, at minimum:

- retain copyright and license notices;
- include an unmodified GFDL 1.2 license copy;
- preserve the same license for modified text;
- identify the modified work and modification history;
- preserve original network locations;
- derive author/history records from exact page revisions;
- check every “unless otherwise noted” page or attachment exception;
- avoid applying Wiki-text rights to images, files, proprietary software, or
  potential data.

The current 81 raw records contain page IDs, revision IDs, wikitext, and HTML,
but no closed author/history/license sidecars. The derived Markdown similarly
lacks the required history and attribution chain.

Current status: `release-blocked`; safe fallback is revision/hash metadata plus
external resolution.

## CP2K 2026.2

### Exact identity

- tag: `v2026.2`
- annotated tag object: `09496e055e132aa3dba53a7751ebdf432b4ebb78`
- peeled commit: `67b5da876dd6a76b8b021d5a04d1c81ba79a4c50`
- manual path: `cp2k-2026_2-branch`

### Official evidence

| Artifact | Official locator | SHA-256 |
|---|---|---|
| Repository root `LICENSE` | `https://raw.githubusercontent.com/cp2k/cp2k/67b5da876dd6a76b8b021d5a04d1c81ba79a4c50/LICENSE` | `8177f97513213526df2cf6184d8ff986c675afb514d4e68a404010521b880643` |
| `docs/conf.py` | `https://raw.githubusercontent.com/cp2k/cp2k/67b5da876dd6a76b8b021d5a04d1c81ba79a4c50/docs/conf.py` | `72e6f813af22aa7e65a01fb47ed4c8e11ce543e4245cf78b9b398302fbd6ee44` |
| `docs/index.md` | `https://raw.githubusercontent.com/cp2k/cp2k/67b5da876dd6a76b8b021d5a04d1c81ba79a4c50/docs/index.md` | `4db714dfed217ac7fc613e70913e9f940f72427dc2ecd2a4867d1830b6b37411` |
| Rendered manual index | `https://manual.cp2k.org/cp2k-2026_2-branch/index.html` | `7adf1572e5b4d2b1eb3f093334f6f8a1f009110b4e1824d8c7828171ada4da47` |

The root repository contains GPLv2 text, and source files commonly carry
GPL-2.0-or-later identifiers. The inspected documentation entry files and
rendered manual pages do not provide a separate documentation license grant.
The release tag also does not, by itself, prove which exact commit generated
each live HTML page.

### Storage decision

- exact `docs/**` source: metadata-only; the repository root GPL file and
  source-file SPDX patterns do not establish a documentation-wide license
  grant, so body materialization remains blocked;
- generated input reference: require the input XML/generator/config/build
  receipt;
- `manual.cp2k.org` rendered HTML or derived full-page text: metadata-only
  until source/build identity and documentation-license scope close;
- CP2K DokuWiki licensing must not be projected onto the separate Sphinx
  manual.

Current status:
`blocked-pending-documentation-license-scope-and-build-provenance`.

## SIESTA

### 5.4.2 release manual and source supplements

Exact identity:

- tag: `5.4.2`
- annotated tag object: `0e2722c2c1fa8dfe8b768b376eeebb4c64db969d`
- peeled commit: `e486d12067b96ff688179f0496d0ec21b6fae0ab`

Official evidence:

| Artifact | Official locator | SHA-256 |
|---|---|---|
| Project code-access/license page | `https://siesta-project.org/siesta/CodeAccess/` | `d94ffd630614bc9298c6b4a6a74c740051884110d6919d2e2f67e2aa639c3f5d` |
| Exact `COPYING` | `https://gitlab.com/siesta-project/siesta/-/raw/e486d12067b96ff688179f0496d0ec21b6fae0ab/COPYING` | `fc82ca8b6fdb18d4e3e85cfd8ab58d1bcd3f1b29abe782895abd91d64763f8e7` |
| Representative `DFT+U.tex` | `https://gitlab.com/siesta-project/siesta/-/raw/e486d12067b96ff688179f0496d0ec21b6fae0ab/Docs/tex/sections/DFT%2BU.tex` | `8d280815708f8e47b6e9328412610dd65b1f770ba2bb411880efb3bdf3490275` |
| `Src/read_options.F90` | `https://gitlab.com/siesta-project/siesta/-/raw/e486d12067b96ff688179f0496d0ec21b6fae0ab/Src/read_options.F90` | `952e3dc3d385f1399f024f332ec22d5dee962efc62280937833471deba1769c8` |

The release `COPYING` file establishes the repository license text but does not
by itself establish that the 47 selected `Docs/tex/**` manual files are
licensed as documentation under that scope. This audit therefore makes no
positive redistribution decision for the TeX manual.

Only six selected source supplements have explicit GPL headers and may proceed
as separately bounded candidates:

- `Src/read_options.F90`
- `Src/scfconvergence_test.F`
- `Src/siesta_analysis.F90`
- `Src/siesta_end.F`
- `Src/siesta_forces.F90`
- `Src/write_subs.F`

Even these six remain metadata-only here: their exact headers, notices, source
identity, material class, transformation, and repository-level distribution
policy must be validated by the materialization adapter.

Current status: `blocked-tex-docs-scope-unproven`; six source supplements are
`candidate-only`, not approved for body materialization.

### Rendered documentation portal

| Artifact | Official locator | SHA-256 |
|---|---|---|
| SIESTA 5.4 rendered manual | `https://docs.siesta-project.org/projects/siesta/en/5.4/reference/siesta.html` | `b2228ffca6ec8a505bab4fcd8caaf9354add02f36fde3fb3d827087f4021926f` |
| `siesta-docs` exact license | `https://gitlab.com/siesta-project/documentation/siesta-docs/-/raw/ca6da4c46538bccce34776cdbb075fa4bfc2c6dc/LICENSE` | `7074fb66818fbbc771e52bb25b0273a586a4ed42bf21c923b7e880cf1a9597e9` |

The `siesta-docs` `5.4` branch currently resolves to commit
`6c58d08b6aef7f1c8d20d85c215e96ce98e47870`. That commit, rather than
`master`, is the source-version pin relevant to a 5.4 provenance investigation.
The exact license file above is pinned separately at
`ca6da4c46538bccce34776cdbb075fa4bfc2c6dc`; it records the terms text at that
source state but does not prove that the hashed rendered portal body was built
from either commit, that its complete source tree is inventoried, or that no
per-file exceptions apply.

The portal corpus therefore remains separate from the 5.4.2 release-source
corpus and metadata-only. This audit records evidence and blockers only; it
does not make a legal conclusion about redistribution obligations.

## Minimal `materialized-open-content-v1` adapter

The first body-materialization adapter must remain provider-neutral and
fail-closed. Its minimum input contract is:

- exact authority, provider, version/tag/commit, and enumerated source-root
  identity;
- exact source URL/path, raw byte length and SHA-256, material class, and
  included/excluded corpus partition;
- documentation-specific terms bytes or content-addressed equivalent,
  exception inventory, reviewer/trust attestation, and a central storage mode
  that explicitly permits body materialization; and
- transformer/dependency identity, selector plan, required notices, and
  repository-level third-party distribution policy.

Its output must preserve immutable raw bytes separately from derived slices and
emit source-to-slice mappings, selected byte hashes/lengths, transformation
records, notices, and a bidirectionally closed loss ledger. It must never fetch
credentials, licensed runtimes, potentials, or content whose authority or
storage decision is unresolved.

Acceptance requires all of the following:

1. two clean runs produce byte-identical output and manifests;
2. every stored byte rehashes to its declared source or selected-slice
   identity, with confined paths and no symlink/hardlink escape;
3. the exact corpus partition, source-to-slice mapping, overlap/orphan checks,
   loss ledger, license/notice sidecars, and third-party exceptions close;
4. wrong revisions, changed bytes, missing notices, unknown documentation
   scope, unlisted third-party content, or absent reviewer authority fail
   before any canonical pack mutation;
5. bundle, strict storage, portable active-only, and full repository audits
   consume the result without promoting lifecycle or scientific maturity.

No current provider satisfies this acceptance summary; the canonical packs
remain metadata-only.

## Cross-provider enforcement requirements

The machine validator must enforce:

1. `raw_text_redistribution: true` requires an exact license URL, exact license
   hash, and matching repository license/COPYING sidecar.
2. `derived_text_redistribution: true` requires a derivative license decision,
   source mapping, transformation identity, and modification notice.
3. Unclear license scope permits metadata only.
4. GFDL-derived pages require revision-bound author/history evidence.
5. NonCommercial material cannot be represented as unrestricted.
6. “Unless otherwise noted” triggers a per-page or per-attachment exception
   scan.
7. Code license, documentation license, website terms, and proprietary runtime
   license are distinct fields.
8. A changed dynamic license/terms hash invalidates the previous clearance.
9. Release validation checks the bytes of the stored license/COPYING and
   notice files, not only their URLs.
10. License clearance never promotes Skill lifecycle or scientific maturity.
