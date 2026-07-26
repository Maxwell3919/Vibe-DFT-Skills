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

## Explicit technical gaps

These items remain explicit and must not be silently promoted to manual
content:

- Multiwfn has two registered external PDF routes whose bodies were not
  technically retrievable through the registered source route. Both remain
  `metadata-only-body-unavailable`.
- The MACE ReadTheDocs search index body is unavailable. The pinned full
  documentation tree is materialized separately, so this missing index does
  not remove the documentation pages themselves.
- Twelve LASP/LOBSTER publisher records are literature provenance, not
  software-manual bodies. They remain `external-publisher-body-not-retrieved`.
- One SIESTA page names two upstream image assets,
  `Interactions.png` and `RectangularMatrix.png`, that are absent upstream.
  The page text and source are retained; the missing images are recorded in
  the provider manifest.
- The VASP main-namespace enumeration records ten requested titles as missing
  or not publicly readable: `Caveat`, `Cite`, `CONSTUCTION:LSEPK`,
  `Extract zpr cd carbon`, `GW0 caveat`, `Meta-GGA`,
  `NMAXFOCKAE and LMAXFOCKAE`, `Style-guide`, `Tempalte:CITE`, and
  `Tempalte:VIDEO`. These upstream outcomes are enumerated rather than replaced
  with guessed content.
- Four Fair-Chem/MACE/NequIP source-tree records are intentionally
  `metadata-only-nonmanual-source-tree`; exact documentation trees are handled
  separately and code trees are not presented to agents as parameter manuals.

Use `python3 tools/sync_official_manual_cache.py --check` and the provider
`--check` commands in each active calculation Skill before relying on this
status after a later refresh.
