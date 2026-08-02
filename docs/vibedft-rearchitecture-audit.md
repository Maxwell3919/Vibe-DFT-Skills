# VibeDFT architecture-level rearchitecture audit

Date: 2026-08-02 (Asia/Shanghai)

Audit branch: `audit/vibedft-rearchitecture-20260802`

## Conclusion

【推断连接】`Vibe-DFT-Skills` should evolve in place into the VibeDFT
scientific core. Its durable value is the combination of scientific intent,
capability/lifecycle routing, contracts, deterministic validation, workflow
evidence, provenance, and claim ceilings. It should not become a general DFT
runtime, a replacement for upstream scientific software, or the long-term
home of the official-document acquisition supply chain.

【推断连接】A separate `Maxwell3919/VibeDFT-Official-Sources` repository is a
sound boundary, but it should be created only after this audit PR is reviewed.
The new repository should own source identity, version binding, capture
methods, manifests, hashes, section/retrieval indexes, and capture receipts.
The core should consume immutable source-release identities and retain the
scientific meaning of those sources: task/capability mapping, parameter
semantics, validation logic, applicability limits, and claim ceilings.

【推断连接】No `NotVibeDFT` module is approved for direct migration by this
audit. A small set of normalized-result ideas, output-event cases, and
anonymizable fixtures deserves a later clean-room comparison. The historical
platform, its code-centric QE task tree, frontend/server, remote/Slurm layer,
and project-specific validators should remain historical.

This is a phase-one inventory and ownership recommendation. It does not create
the new repository, move files, rename the current repository, alter runtime
installation, change scientific acceptance criteria, or authorize deletion of
`NotVibeDFT`.

## Evidence and authority baseline

### Research-Ops

【已独立验证，GitHub API and local Git identity, 2026-08-02】

- GitHub authority: `Maxwell3919/Research-Ops@main`
- reviewed commit: `62b2fa568b09f02e3c3461ae45d7a1a4fa0d54f0`
- Talos mirror: the private operational path recorded in Research-Ops
- local `HEAD == origin/main == GitHub main`; the main worktree was clean
- required records read: `README.md`, `policies/github-main-ops.md`,
  `projects/current-work.yaml`, `projects/vibe-dft-skills.yaml`,
  `tasks/TASK-2026-DFT-CAMPAIGN-EFFICIENCY-LEARNING.yaml`,
  `handoffs/2026-08-01-vibe-dft-skills-crawl4ai-source-ingestion.md`, and
  `handoffs/2026-07-30-notvibedft-repository-rename.md`

Research-Ops remains a control plane. It is not the source authority for this
repository, the future official-source repository, runtime state, manual
bodies, scientific inputs/outputs, or scientific acceptance.

### Vibe-DFT-Skills source and runtime

【已独立验证，GitHub API, local Git, and symlink inspection, 2026-08-02】

- source authority: `Maxwell3919/Vibe-DFT-Skills@main`
- reviewed source commit: `d9f4fdb836540684ebd18b30a6c510217da4aaaa`
- reviewed tree: `614d84d32fff6dc4a559e543bd531434f67128c8`
- GitHub state: public, unarchived, default branch `main`
- GitHub refs: only `main`; open pull requests: zero before this audit branch
- canonical Talos checkout: the source path recorded in Research-Ops
- pre-audit checkout state: clean `main`, exactly aligned with GitHub
- inventory: 1,240 tracked files, 44,694,477 tracked bytes
- lifecycle inventory: 26 source-backed Skills, 7 active and 19 development
- official-source-related inventory: 467 paths selected by the bounded path
  expression `official|manual-cache|source-pack|crawl|capture|document-fetch`

The canonical checkout also has seven protected historical worktrees and a
preserved html2md `stash@{0}`. They were inspected but not changed, applied,
merged, or retired.

【已独立验证，local Git and symlink inspection, 2026-08-02】The installed
runtime source remains a separate clean checkout at
the separately recorded runtime checkout at
`b40e8b3c929a2a0a662b79054916a7e874cdcde5`.
All seven installed active Skill symlinks target that checkout. Source
rearchitecture planning does not update or validate the runtime.

### NotVibeDFT

【已独立验证，GitHub API and local Git, 2026-08-02】

- historical repository: `Maxwell3919/NotVibeDFT`
- GitHub state: private, archived, default branch `main`
- GitHub main: `bbf212e0cba3abe695faef5e568a0a74d990e045`
- reviewed main tree: `59bd75012434482985833a1cd285449689249261`
- GitHub refs: only `main`; open pull requests: zero
- GitHub main inventory: 572 tracked files, 2,774,987 tracked bytes
- no repository-local `AGENTS.md` exists
- Talos checkout: the historical checkout path recorded in Research-Ops
- local checkout is clean but is on the unpublished one-commit branch
  `agent/b0.5-reproducible-runtime-baseline@4cee68d14f2dea5095f30ffde2f0b17ee629d344`

The local-only commit changes 30 files with 1,650 insertions and 77 deletions.
It is recoverable evidence, not GitHub authority and not an accepted migration
source.

【来源记录，GitHub Actions】The latest workflow for exact GitHub main
`bbf212e0` is run
[`28536334270`](https://github.com/Maxwell3919/NotVibeDFT/actions/runs/28536334270)
and concluded `failure`. Python 3.9 failed during test collection because
`src/vibedft/main/commands.py` used PEP 604 union syntax while the package
declared Python `>=3.9`; fail-fast cancelled the other test matrix jobs. A
fresh local test could not be started because the current audit environment
lacks `pytest`. Therefore test files are evidence of intended coverage, not a
current passing acceptance receipt.

## Target responsibility model

```text
scientific intent
  -> task planner
  -> capability router
  -> execution contract
  -> deterministic validation
  -> evidence/provenance package
```

The VibeDFT core owns this chain. It may invoke external tools through narrow,
versioned adapters, but does not absorb their general workflow engines,
scientific implementations, databases, or manual corpora.

```text
official source identity
  -> version binding
  -> capture request/receipt
  -> manifest + content hash
  -> section/retrieval index
  -> immutable source release
```

`VibeDFT-Official-Sources` owns this supply chain. It does not decide which
calculation is scientifically valid, run a workflow, validate a calculation,
or encode Skill logic.

The cross-repository interface should be one-way and hash-bound:

```text
VibeDFT-Official-Sources release/commit
  -> source-manifest ID + schema version + content hashes
  -> VibeDFT core consumer pin
  -> task/capability mapping + scientific validator
```

Large or redistributability-sensitive source bodies stay outside Git in a
content-addressed store. Git contains code, schemas, metadata, manifests,
indexes, receipts, tests, and source-to-commit mapping only.

## Current Vibe-DFT-Skills classification

The table describes future ownership, not an instruction to move every file
matching a directory name mechanically.

| Current path or family | Current type | Future ownership | Phase-one decision |
|---|---|---|---|
| `skills/` | Skill contracts, code-specific guidance, deterministic CLIs, fixtures, and source-pack metadata | Core, after separating source-supply metadata | Retain. Refactor by scientific task over time; do not bulk rename or delete code-specific Skills in the audit PR. |
| `registry/skill-registry.yaml` | Skill lifecycle and routing identity | Core capability registry | Retain as a current authority until a reviewed schema migration. |
| `registry/software-registry.yaml` | Software identity and activation profiles | Core capability registry | Retain. Software selection remains registry-driven. |
| `registry/operation-routes.yaml`, `interface-registry.yaml`, `semantic-obligations.yaml`, `active-evidence.yaml` | Routing, contracts, evidence, and lifecycle gates | Core | Retain and later normalize under `core/router/registry/provenance`. |
| `registry/official-source-authorities.yaml` | Source identity, versions, providers, URLs, and receipts | Official Sources | Migrate in phase two, preserving exact blob/commit mapping. Core keeps only consumer pins and scientific applicability mappings. |
| `registry/document-fetch-adapters.yaml` | Capture-provider and route metadata | Official Sources | Migrate. It is a source-acquisition adapter, not a calculation adapter. |
| `registry/official-document-storage-discovery.yaml` | Source/cache storage discovery | Official Sources | Migrate metadata and policy; runtime body locations remain outside Git. |
| `registry/official-document-consumers.yaml` | Skill-to-document consumption graph | Split | Generic source IDs/pins belong in Official Sources; task/Skill semantic consumption and claim ceilings remain in Core. |
| `registry/official-document-bundle-expectations.yaml` | Pack completeness/topology expectations | Split | Generic manifest topology moves; scientific-consumer coverage and release gates remain in Core. |
| `contracts/web-source-capture-*.schema.json` | Capture request and receipt contracts | Official Sources | Migrate with compatibility fixtures and source commit mapping. |
| `contracts/official-source-record.schema.json`, `official-document-source-catalog*.schema.json`, `official-corpus-manifest*.schema.json` | Source identity and corpus contracts | Official Sources | Migrate. Core consumes released versions rather than owning parallel copies. |
| `contracts/document-slice-manifest*.schema.json` | Source section mapping | Official Sources, with a Core consumer mapping | Move generic section identity/retrieval fields; keep scientific interpretation outside the schema. |
| `contracts/skill-document-coverage*.schema.json`, `skill-document-scope-inventory.schema.json` | Skill-specific evidence/coverage | Core | Retain because these encode consumer completeness and claim ceilings, not just capture facts. Rebind them to external source manifest IDs. |
| `contracts/workflow-*`, `execution-*`, `run-manifest`, `evidence-record`, `calculation-record-envelope`, `normalized-dataset`, `validation-report` | Scientific workflow, execution, evidence, normalization, and validation contracts | Core | Retain. Contract consolidation must preserve separate execution, numerical, physical, postprocessing, and scientific gates. |
| `tools/crawl4ai_capture.py`, `document_fetch_adapters.py`, `sync_official_manual_cache.py`, `check_official_source_drift.py` | Source ingestion/crawl/cache operations | Official Sources | Migrate after the new schemas and policies exist. Browser remains a bounded fallback. |
| `tools/official_source_authorities.py`, `official_document_materialization.py`, `build_official_document_packs.py`, source catalog migrations | Source manifest/materialization pipeline | Primarily Official Sources | Migrate source identity, capture, manifest, and index production. Retain only Core consumer validation/projection logic. |
| `tools/validate_official_document_coverage.py`, `validate_official_document_bundles.py`, dashboards | Mixed supply-chain and Skill-consumer validation | Split | Separate source manifest integrity from scientific consumer coverage. Do not duplicate one validator in both repositories. |
| `tools/validate_contract.py`, `validate_semantics.py`, `validate_candidate.py`, `validate_promotion.py`, `vibedft_readiness.py` | Deterministic contract/scientific/lifecycle checks | Core validators | Retain. |
| `tools/manage_calculation_workspace.py`, `create_run_manifest.py`, `operation_routes.py` | Workflow/evidence preparation | Core workflows/provenance | Retain. They do not establish native execution or scientific acceptance. |
| `tests/test_crawl4ai_capture.py`, official-source authority/drift/materialization/cache tests | Source supply-chain tests | Official Sources | Migrate with implementation and preserve negative fixtures. |
| Skill and repository tests for calculations, convergence, normalized datasets, routing, promotion, and acceptance boundaries | Scientific/core tests | Core | Retain. |
| `requirements-crawl4ai.txt` and `.github/workflows/official-source-drift.yml` | Source acquisition dependency/CI | Official Sources | Migrate; Core should not install a browser crawler for ordinary validation. |
| `skills/*/references/official-source-pack/corpus-*.json` and `slices-*.json` | Large metadata-only source inventories and slice receipts | Official Sources | Migrate and deduplicate by source identity. Some individual JSON files exceed 2 MiB despite containing no manual body. |
| `skills/*/references/official-source-pack/scope-inventory.json`, `coverage.json`, `bundle.json` | Mixed source and Skill-consumer projections | Split | Generic source records move; task coverage and exact consumer pins remain or are regenerated in Core. |
| `skills/*/references/manual-cache-receipts/` and provider source registries | Capture receipts/indexes | Official Sources | Migrate after privacy/redistribution review; Core retains immutable references only. |
| provider-specific `sync_official_manuals.py`, `resolve_official_sources.py`, `html2md_adapter.js` | Crawl/transform/resolver code | Official Sources | Migrate only after common adapter contracts remove Skill-local duplication. |
| QE parameter/output guards, DFT postprocessing, CIF analysis, convergence and provenance scripts | Scientific parser/validator logic | Core | Retain as deterministic checks or future calculation adapters. |
| `golden-bundles/` and legally reusable synthetic fixtures | Scientific contract fixtures | Core | Retain; do not confuse synthetic fixture passage with native/scientific acceptance. |
| `docs/official-*`, `docs/crawl4ai-*` | Mixed architecture, supply-chain, and status documentation | Split | Historical audit/handoff stays with its repository history. Current acquisition policy moves; Core keeps consumer/scientific boundary docs. |

## Target core shape and migration constraints

The requested target layout is directionally correct:

```text
core/        scientific intent and stable domain models
planner/     task decomposition and observable-first planning
router/      capability and adapter selection
registry/    capability, lifecycle, software and interface identities
schemas/     versioned public contracts
provenance/  evidence identities and lineage
skills/      concise task-oriented Agent contracts
adapters/    code/tool/engine integrations
validators/  deterministic scientific and contract checks
workflows/   task-level compositions, not a general process engine
contracts/   compatibility location during schema migration
tests/
docs/
```

This should be achieved by compatibility-preserving increments, not a single
directory reshuffle. `contracts/` should remain authoritative until a schema
registry/version migration makes `schemas/` unambiguous; similarly, current
Skill IDs remain valid until registry aliases, consumer pins, installation,
and runtime compatibility are tested.

### Task-oriented Skills

The target task taxonomy is preferable to multiplying code/task pairs:

- `structural-relaxation`
- `electronic-structure`
- `phonon`
- `electron-phonon-coupling`
- `defects`
- `interfaces`

These Skills express scientific intent, required evidence, convergence axes,
and acceptance boundaries. The router selects QE/VASP/CP2K/SIESTA or an
external tool from capability declarations. Existing code-specific rigorous
Skills should initially become provider adapters/reference implementations;
they should not be deleted until task-oriented contracts reach equivalent or
stronger evidence coverage and installed-runtime compatibility is proven.

## Duplicate capability and complexity analysis

The architectural test is not whether code exists, but whether VibeDFT has a
distinct scientific contract that upstream software does not provide.

| Capability | Existing/upstream capability | Current duplication risk | Recommendation |
|---|---|---|---|
| Durable execution, remote computers, scheduler lifecycle, checkpointed workflows, provenance graph | AiiDA documents external-code `CalcJob`, checkpointed `WorkChain`, daemon execution, and data/logical provenance | A home-grown scheduler/transport/process engine would duplicate a mature state machine and provenance store | Keep VibeDFT execution/acceptance contracts; implement a narrow adapter pilot rather than a new engine. |
| QE execution, restart/error handling, parsed outputs | `aiida-quantumespresso` provides `PwBaseWorkChain` with automated error handling/restarts and structured outputs | Rebuilding a complete QE runtime/parser matrix has high maintenance and version-drift cost | Preserve VibeDFT scientific gates; reuse upstream execution/parser facts where they meet a versioned adapter contract. |
| Calculator input/output and structure I/O | ASE exposes an Espresso calculator and `espresso-in`/`espresso-out` I/O | Generic structure/converter/parser reimplementation adds compatibility burden | Prefer ASE/pymatgen-style adapters for general representation; keep only VibeDFT-specific provenance and fail-closed scientific checks. |
| Materials workflow recipes and dynamic flows | atomate2/jobflow and quacc provide jobs/flows and existing calculator recipes | General DAG/recipe infrastructure is not a VibeDFT differentiator | Keep task plans and evidence contracts software-neutral; adapt an upstream engine where execution is required. |
| CIF parsing, symmetry, neighbor search, structure construction | Gemmi, PyCifRW, ASE, spglib, and pymatgen already implement core algorithms | Reimplementing file formats and crystallographic algorithms is unnecessary risk | Retain VibeDFT traceability, uncertainty/disorder checks, manifests, and fail-closed screens as compositions around upstream libraries. |
| Bands/DOS/phonon parsing and plotting | ASE/pymatgen, sumo, pyprocar, phonopy and code-native tools cover many formats | Parallel format-specific implementations can drift | Registry-select an upstream/native backend; retain normalization, provenance, maturity, and scientific acceptance checks. |
| Official manual mirroring/crawling | Provider APIs/Git/HTTP/PDF plus generic crawl tooling | Skill-local crawlers, caches, pack builders, and receipts repeat across 26 Skills | Centralize acquisition in Official Sources; Core stores only consumer pins and scientific mappings. |

Primary upstream references reviewed for this decision:

- [AiiDA provenance concepts](https://aiida.readthedocs.io/projects/aiida-core/en/stable/topics/provenance/concepts.html)
- [AiiDA process concepts](https://aiida.readthedocs.io/projects/aiida-core/en/stable/topics/processes/concepts.html)
- [aiida-quantumespresso `PwBaseWorkChain`](https://aiida-quantumespresso.readthedocs.io/en/latest/reference/workflows/pw/base.html)
- [ASE Espresso calculator source documentation](https://docs.ase-lib.org/_modules/ase/calculators/espresso.html)
- [atomate2 workflow introduction](https://materialsproject.github.io/atomate2/user/index.html)
- [quacc workflow concepts](https://quantum-accelerators.github.io/quacc/user/recipes/workflows.html)

These references establish available upstream surfaces, not automatic fitness
for this repository. Adapter adoption still requires version pinning,
provenance, failure semantics, deterministic fixtures, and maturity evidence.

## VibeDFT-Official-Sources boundary recommendation

### Own

- official source and provider identity
- exact/range/channel version binding
- URL, API, Git, PDF, browser and other capture route declarations
- crawl/capture request and receipt schemas
- manifest, byte count, content hash, final URL, retrieval time and method
- section identity and retrieval index
- transform identity and input/output hashes
- redistribution classification and fail-closed exclusions
- source release and source-to-origin commit/blob mapping
- synthetic public tests for parsing, schema and capture failure behavior

### Do not own

- scientific intent or task planning
- capability selection for a calculation
- scientific parameter interpretation
- calculation execution or workflow state
- calculation parser acceptance
- convergence, physical-validity or scientific-acceptance gates
- Skill lifecycle or promotion

### Initial structure refinement

The requested initial structure is suitable. Add two machine-readable
artifacts before migrating data:

```text
registry/migration-map.yaml
schemas/retrieval-index.schema.json
```

`migration-map.yaml` should record, for every migrated file or generated
record:

- source repository and source commit
- source path and Git blob OID
- destination path and destination commit
- transformation identifier, if any
- before/after SHA-256
- disposition: copied, split, regenerated, superseded, or retained-in-core

This preserves provenance without rewriting the history of either existing
repository or requiring a force push.

## Phased migration plan and gates

### Phase 1 — audit PR (this change)

- add this architecture audit
- add `docs/notvibedft-retirement-audit.md`
- run the existing five-command validation chain
- create a PR and do not merge

Exit: reviewed inventory and ownership decisions. No source movement.

### Phase 2 — create Official Sources

- create the repository with policies, schemas, empty registries, tests, and
  migration-map contract
- validate schema parsing, registry loading, manifest loading, and tests
- migrate source identity/capture/receipt code in small commits
- keep source bodies outside Git
- record exact origin commit/blob mappings

Exit: the new repository can emit a deterministic source release that the
core can pin, without changing a scientific result or claim.

### Phase 3 — switch Core consumers

- add external source release pins and compatibility checks
- regenerate consumer coverage from external manifests
- stop dual-writing source authority/capture receipts
- move source-ingestion CI and dependencies
- remove old source-supply files only after exact parity, rollback mapping,
  and runtime independence are verified

Exit: one source of truth for acquisition metadata; no duplicate writer.

### Phase 4 — task-oriented core

- introduce task contracts and router interfaces without renaming the repo
- map existing code-specific Skills to adapters
- preserve installed Skill IDs through explicit compatibility aliases
- consolidate validators and normalized result/evidence contracts
- pilot one observable end to end before widening the taxonomy

Exit: a task-oriented plan can select a versioned adapter and emit a validated
evidence package while scientific acceptance remains separate.

### Phase 5 — NotVibeDFT retirement decision

- first preserve GitHub main, the local-only commit, refs, CI evidence, and a
  verified recovery bundle/manifest
- complete any approved clean-room extraction with independent tests
- independently verify the archive and migration map
- only then ask for an explicit user decision on deletion

Exit: deletion is a separate destructive decision. This audit does not
recommend or authorize it now.

## Risks and controls

| Risk | Current evidence | Control |
|---|---|---|
| Authority split-brain | Source metadata and scientific consumption currently coexist in Skill-local packs | Establish one writer per record family and immutable cross-repository pins before removing anything. |
| Runtime incompatibility | Installed runtime is still `b40e8b3`, behind source `d9f4fdb` | Treat runtime migration as a separate reviewed task with exact Skill ID/CLI compatibility tests. |
| Scientific gate regression | Directory moves can silently weaken validation or claim ceilings | Require before/after fixture parity and preserve execution, numerical, physical, postprocessing, and scientific gates separately. |
| Source body/redistribution risk | Current design uses large metadata inventories and external bodies; some providers are restricted | Keep bodies outside Git, prohibit commercial/manual body copies, and require `redistribution.md` decisions per source class. |
| Dual-writer drift | Copy-first migrations can leave both repositories authoritative | Time-limit compatibility mirrors and fail CI if both sides claim write authority. |
| Git provenance loss | A new repository starts with new commit IDs | Record source commit, blob OID, hashes, transformation and destination commit in a migration map. |
| Historical code promotion | NotVibeDFT has extensive code and tests but failing exact-main CI | Require bounded independent review; never promote based on file existence or historical intent. |

## Phase-one decision

【推断连接】This audit PR is suitable for review but should not be merged until
the ownership split, cross-repository pin contract, and NotVibeDFT candidate
dispositions are accepted. Creating `VibeDFT-Official-Sources` is the next
reversible step after that review. Deleting `NotVibeDFT` is not a next-step
action.
