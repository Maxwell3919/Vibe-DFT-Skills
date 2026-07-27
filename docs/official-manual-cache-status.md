# Official-manual cache verification status

This status records the technical local-cache verification completed on
2026-07-26 UTC. It does not claim that an external executable is installed,
that a manual matches an unrecorded executable version, or that documentation
alone supports a scientific result.

## Verified local materialization

- 26/26 source-backed Skills have an `official-source-pack` and a generated
  `references/manual-cache-route.md`.
- The unified local cache contains 14,635 strict UTF-8 Markdown or
  metadata-route documents. Its independent `--check` passed with no recorded
  live drift or pinned-source mismatch.
- Conversion uses the pinned `helloworld-Co/html2md` tool for HTML. RST is
  rendered before conversion and retains a lossless source appendix. Markdown,
  source text, JSON, and PDF extraction use format-specific lossless or
  byte-bound routes.
- Repository-tracked legacy official-document body artifacts are zero. Compact
  receipts, exact hashes, source catalogs, routing documents, and deterministic
  tooling remain in Git; full provider bodies remain in the local cache.

The final per-Skill document counts are:

| Skill | Documents |
|---|---:|
| catmap-microkinetics | 41 |
| cif-structure-analysis | 10 |
| cp2k-rigorous-calculations | 3,033 |
| deepmd-rigorous-workflows | 212 |
| dft-campaign-efficiency | 3 |
| dft-hpc-execution | 15 |
| dft-postprocess | 5,801 |
| dft-project-orchestrator | 3 |
| dft-reporting | 1 |
| dft-review-response | 1 |
| dft-structure-preparation | 487 |
| gaussian-rigorous-calculations | 7 |
| gpumd-rigorous-simulations | 197 |
| gromacs-rigorous-simulations | 326 |
| lammps-rigorous-simulations | 1,032 |
| lasp-rigorous-simulations | 5 |
| literature-to-dft-plan | 1 |
| lobster-bonding-analysis | 7 |
| ml-potential-workflows | 233 |
| multiwfn-wavefunction-analysis | 2 |
| ovito-atomistic-analysis | 217 |
| phonopy-rigorous-workflows | 49 |
| qe-rigorous-calculations | 1,672 |
| siesta-rigorous-calculations | 158 |
| vasp-rigorous-calculations | 1,091 |
| vaspkit-postprocess | 31 |

## Full provider checks

- CP2K 2026.2: 3,030 pages, including 2,946 genindex-discovered pages
  and 84 linked pages; 66,791 internal links passed.
- SIESTA 5.4.2: all 104 source documents are represented as 89 rendered
  pages plus 15 source-only pages; 1,333 internal links passed.
- Quantum ESPRESSO: 36 executable input manuals with 1,231 sections, 5
  user guides with 95 pages, 121 release-note sections, and 11 PDF manuals
  with 171 pages passed.
- VASP Wiki: the complete public main-namespace inventory resolved 1,287 of
  1,297 requested titles into 1,091 unique pages; the provider reports
  `upstream_universe_complete=true` and `public_body_complete=true`.

## Explicit gap ledger

The ledger was reviewed on 2026-07-27. Its identifiers are stable across later
refreshes: close an item by recording new provider evidence against the same
identifier rather than deleting the historical gap. No item may be silently
promoted to manual content.

| Gap ID | Provider and scope | State | Current usable evidence | Closure condition |
|---|---|---|---|---|
| `OM-GAP-001` | Multiwfn, two registered external PDF routes | `blocked-body-unavailable` | Route metadata and source identity only | Retrieve both bodies through the registered first-party route, bind exact receipts, render them, and pass character/hash checks |
| `OM-GAP-002` | MACE ReadTheDocs search index | `compensated-index-unavailable` | The pinned full documentation tree is materialized; only the search-index body is absent | Bind and verify the official index body, or record an upstream statement that the index is no longer published |
| `OM-GAP-003` | Twelve LASP/LOBSTER publisher records | `intentional-literature-metadata` | Bibliographic provenance only; these records are not software manuals | Reclassify only if a first-party software-manual body is published and registered |
| `OM-GAP-004` | SIESTA `Interactions.png` and `RectangularMatrix.png` | `blocked-upstream-assets-absent` | Referencing page text and source are retained | Upstream publishes the two assets and their identities are added to the provider manifest |
| `OM-GAP-005` | Ten VASP Wiki requested titles | `blocked-missing-or-not-public` | Exact title-level provider outcomes | Each title resolves to a public first-party page, or the provider publishes an authoritative deletion/rename mapping |
| `OM-GAP-006` | Four Fair-Chem/MACE/NequIP source-tree records | `intentional-nonmanual-boundary` | Exact documentation trees are handled separately; source-tree identity remains metadata | No closure is required unless a source-tree path becomes the first-party parameter manual |

For `OM-GAP-005`, the recorded titles are `Caveat`, `Cite`,
`CONSTUCTION:LSEPK`, `Extract zpr cd carbon`, `GW0 caveat`, `Meta-GGA`,
`NMAXFOCKAE and LMAXFOCKAE`, `Style-guide`, `Tempalte:CITE`, and
`Tempalte:VIDEO`. The spelling is preserved from the provider enumeration.

The ledger distinguishes missing manual evidence from intentional scope
boundaries. `OM-GAP-003` and `OM-GAP-006` prevent literature or code trees from
being misrepresented as parameter manuals; they are not requests to copy those
bodies into the repository.

Use `python3 tools/sync_official_manual_cache.py --check` and the provider
`--check` commands in each active calculation Skill before relying on this
status after a later refresh.
