# NotVibeDFT retirement and recovery audit

Date: 2026-08-02 (Asia/Shanghai)

Reviewed GitHub authority:
`Maxwell3919/NotVibeDFT@bbf212e0cba3abe695faef5e568a0a74d990e045`

Separately reviewed local-only commit:
`4cee68d14f2dea5095f30ffde2f0b17ee629d344`

## Conclusion

【推断连接】`NotVibeDFT` should remain an archived historical implementation.
It should not become the base of the new VibeDFT architecture and should not
be merged wholesale into `Vibe-DFT-Skills`.

No module currently satisfies all three direct-migration gates:

1. absent from the current core;
2. not substantially covered by a mature upstream implementation; and
3. supported by current, passing, independently reviewed tests under a clear
   and portable boundary.

A small number of ideas and test scenarios warrant a later clean-room
extraction review. That means re-expressing a bounded contract or anonymized
fixture against current VibeDFT interfaces, not copying the historical package
tree.

Deletion is not authorized. The GitHub main, local-only commit, recovery
bundle, refs, CI evidence, and any accepted extraction mapping must be
independently verified before a later delete decision is presented to the
user.

## Repository state

【已独立验证，GitHub API, GitHub Actions, and local Git, 2026-08-02】

- repository: `Maxwell3919/NotVibeDFT`
- visibility/state: private and archived
- default/only GitHub branch: `main`
- GitHub main: `bbf212e0cba3abe695faef5e568a0a74d990e045`
- main tree: `59bd75012434482985833a1cd285449689249261`
- open pull requests: zero
- main inventory: 572 tracked files and 2,774,987 tracked bytes
- main top-level concentration: 326 files under `src/`, 166 under `tests/`,
  39 under `plugins/`, and 17 under `docs/`
- no repository-local `AGENTS.md`

The README declares a QE-first v2 platform with `main`, `calculator`,
`structure`, `analysis`, and `_shared` as canonical, while retaining many
legacy modules. GitHub main contains 116 tracked files under the calculator
package but also 31 under legacy `core`, 19 under `generators`, 19 under
`frontend`, 14 under `analyzers`, 13 under `research`, 11 under `validators`,
and multiple other legacy trees. The implementation is therefore not a clean
five-layer package even by its own stated boundary.

### Unmerged local work

【已独立验证】The Talos checkout is clean but is not on GitHub main. It is on:

```text
agent/b0.5-reproducible-runtime-baseline
  @ 4cee68d14f2dea5095f30ffde2f0b17ee629d344
```

The local-only commit adds a Skills compatibility trust root, governance
command bridge, workspace bridge, parameter-plan hardening, Slurm validation,
and tests. Its diff relative to main is 30 files, 1,650 insertions, and 77
deletions. It is recoverable local evidence but was never published or
accepted. It must not be silently pushed, merged, rebased, or used as the
source of a future architecture.

Research-Ops records an exact private recovery-bundle path. The path is not
copied into this public repository.

This audit did not alter or re-verify the bundle contents. Bundle recovery is
therefore 【未知/待验证】 for a future destructive-action gate.

## Test evidence boundary

【来源记录】GitHub Actions run
[`28536334270`](https://github.com/Maxwell3919/NotVibeDFT/actions/runs/28536334270)
targets exact GitHub main `bbf212e0` and failed. Python 3.9 encountered nine
collection errors because `str | Path` was evaluated even though the package
declared Python `>=3.9`; fail-fast cancelled the other matrix test jobs. The
privacy job passed, but it does not establish software correctness.

【未知/待验证】A fresh local test run was not available. The active audit Python
environment has no `pytest`, so the attempted bounded suite stopped before
collection with `No module named pytest`. No dependency installation was
performed for this read-only retirement audit.

Consequently, the repository's tests establish fixture and intended-interface
inventory. They do not establish that any candidate module is currently
accepted, portable, or compatible with the VibeDFT core.

## Module disposition

“Migrate” below means direct code movement. “Extract” means a new bounded
implementation or fixture written against current contracts after a separate
review.

| Historical module | Direct migration | Later extraction candidate | Reason |
|---|---:|---:|---|
| `src/vibedft/_shared/contracts.py` (`Evidence`, `Provenance`, `Diagnostics`, `Readiness`, `CleanedResult`, `ReviewResult`) | No | Yes, contract-delta review only | The concepts are useful, but current VibeDFT already has versioned `evidence-record`, `calculation-record-envelope`, `normalized-dataset`, `validation-report`, workflow and run schemas with stricter claim separation. Copying dataclasses would create a second contract authority. |
| `src/vibedft/analysis/{contracts,cleaned,routing}.py` | No | Possibly one consumer fixture | It consumes `CleanedResult`, but overlaps the current `dft-postprocess` normalization/analysis layer and encodes a historical result shape. Preserve only unique negative/blocked consumer cases if independently identified. |
| `src/vibedft/main/{commands,envelopes,cli}.py` | No | No | It is a code/task-specific CLI registry (`qe.scf.review`, `qe.dos.review`, etc.), contrary to the new task-oriented, registry-selected adapter architecture. Current tools already expose deterministic JSON CLIs. |
| `src/vibedft/calculator/qe/common/output_events.py` | No | Yes | Bounded output-event normalization and message sanitization may supply missing cases, but current `qe_guard.py` and `dftpost` already parse QE completion/convergence/output facts. Compare behavior and port only unique anonymized fixtures. |
| `src/vibedft/calculator/qe/scf/` | No | Select fixtures only | The parser alone is over 1,100 lines and duplicates current QE input/output gates plus upstream QE/ASE/AiiDA surfaces. Review scientific distinctions, do not transplant the task package. |
| `src/vibedft/calculator/qe/relax/` and `vc_relax/` | No | Select fixtures only | Current core already distinguishes structure/output/convergence evidence; upstream adapters cover execution/parsing. Any unique cell/force/stress failure case should become an anonymized fixture against a task-oriented structural-relaxation contract. |
| `src/vibedft/calculator/qe/{nscf,bands,dos,pdos,pp}/` | No | Select output fixtures only | These are code-specific task packages and overlap current `dft-postprocess` and native/upstream parsers. They also duplicate review/clean logic per task. Preserve only demonstrably unique malformed/truncated/version cases. |
| `src/vibedft/calculator/qe/phonon/` | No | No at present | `clean.py` is five lines and the repository describes the route as scaffolding. Stage naming is design evidence, not a mature EPC/phonon implementation. |
| `src/vibedft/parsers/qe_input_parser.py` | No | Possibly negative fixtures | A 557-line general QE input parser duplicates the current official-document-bound QE guard and upstream parsers. Only parser counterexamples absent from current tests may be useful. |
| `src/vibedft/validators/{pw,ph,q2r,matdyn,lambda,two_d}.py` | No | Case-by-case rule comparison | General rules overlap current QE rigorous/EPC validators; direct copying risks changing acceptance semantics. A rule may be reimplemented only after official-source binding and before/after evidence review. |
| Project/material-specific validator modules | No | No | Project/material-specific and unsuitable for a portable public core. They also risk carrying unpublished numerical assumptions. |
| `src/vibedft/properties/`, `postprocess/`, `epw/`, `spin/`, `convergence/` | No | Case-by-case fixture comparison | Current `dft-postprocess` and rigorous-code Skills already own normalized observables, provenance and maturity gates. Mature upstream tools cover much of the format/physics machinery. Avoid parallel implementations. |
| `src/vibedft/structure/` and legacy structure helpers | No | No code; compare tests only | ASE, pymatgen, Gemmi, PyCifRW and spglib provide the algorithms; current CIF/structure Skills add traceability and scientific screens. The historical code has no unique accepted portable boundary. |
| `src/vibedft/core/{remote,slurm,workflow_executor}.py` | No | No | The README calls remote commands `PLAN ONLY`; durable authorization, leases, scheduler events, unknown submission handling, restart and cancellation are absent. AiiDA/jobflow/quacc cover mature runtime surfaces. |
| `src/vibedft/core/registry.py`, generators and workflow plans | No | Possibly parameter-plan fixture | Code-specific profile/planner logic conflicts with the new capability registry. The unpublished baseline tightens it, but is not authority and mixes runtime/site concerns. |
| `src/vibedft/main/governance_commands.py`, `workspace.py`, `_shared/skills_compatibility.*` from local-only `4cee68d` | No | No direct migration | These hard-bind the historical package to a past Skills tree and duplicate canonical contract/workspace tools. The commit is unpublished and current source has moved beyond its reviewed identities. |
| `src/vibedft/agent/`, `analyzers/`, `classifiers/`, `semantics/`, `decision/` | No | No | They embody the old platform's agent/application architecture and often duplicate scientific decision layers. The new core should expose contracts and deterministic validators rather than migrate opaque decision agents. |
| `src/vibedft/frontend/`, `server/` | No | No | Frontend/API storage is outside the requested scientific core and has mature upstream alternatives. No current need justifies carrying it. |
| `src/vibedft/research/` and material-specific recipes/reports | No | No | Project-specific research state and fixtures do not belong in the portable core. |
| `plugins/`, `profiles/`, `config/parameter.schema.yaml`, `workflows/` | No | Inspect one schema at a time only if a current gap exists | They mix historical profiles, code-specific workflow stages and platform configuration. Future capability schemas should be designed from current requirements, not inherited wholesale. |
| `tests/qe/**` synthetic pass/warn/block cases | No as a tree | Yes, after anonymization and deduplication | These are the strongest recovery candidates because they can expose parser/gate edge cases. Each must be checked for uniqueness, source provenance, licensing, real material names, and scientific threshold assumptions. |
| `tests/fixtures/**` | No as a tree | Restricted subset only | Many fixtures contain real material/project identifiers and historical research samples. Direct migration would violate the new repository's anonymized-fixture boundary and may expose unpublished context. |

## Required component checks

### Parser

【来源记录】The repository contains a general QE input parser and multiple
task/output parsers. 【推断连接】They should not migrate directly because the
current core already has QE guards/postprocessing parsers and because upstream
ASE/AiiDA QE integrations cover general execution/output surfaces. The useful
unit of recovery is a failing input/output example, not the historical parser
package.

### Normalized result schema

【来源记录】`CleanedResult`, `ReviewResult`, `Evidence`, `Provenance`,
`Diagnostics`, and downstream `Readiness` dataclasses exist, with analysis and
CLI consumers. 【推断连接】The conceptual separation is worth comparing, but
current JSON Schemas already provide a stronger cross-code authority and keep
technical facts separate from human scientific acceptance. No direct schema
migration is justified.

### Validator

【来源记录】Both general QE validators and project-specific validators exist.
【推断连接】General rules require an official-source and behavior comparison;
project-specific rules remain historical. A passing historical unit test would
still not justify changing a current scientific acceptance criterion.

### Execution contract

【来源记录】The old platform contains command envelopes, calculator stages,
remote/Slurm helpers, and an unpublished Skills compatibility/workspace bridge.
Its own documentation states that remote commands are plan-only and that
authorization, durable scheduler state, retry/cancel, and unknown-submission
reconciliation are absent. 【推断连接】It is not a reusable runtime contract.

### Fixture

【来源记录】There are extensive synthetic and historical fixtures. The QE
pass/warn/block cases may have regression value. 【推断连接】Only anonymized,
license-safe, unique cases should be recreated in the current repository; the
historical fixture tree should not be copied.

## Mature upstream overlap

- AiiDA already supplies durable process execution, checkpointed workflows,
  scheduler/transport integration patterns, and provenance graphs.
- `aiida-quantumespresso` supplies QE workchains with automated restart/error
  handling and structured outputs.
- ASE supplies structure representation, QE input/output I/O, and calculator
  integration.
- atomate2/jobflow and quacc supply task/flow abstractions and reusable
  materials-workflow recipes.
- pymatgen, phonopy, sumo, pyprocar, spglib, Gemmi and PyCifRW cover major
  portions of structure, symmetry, phonon, electronic-output, and file-format
  functionality.

This overlap does not eliminate VibeDFT's role. It narrows that role to
scientific intent, capability routing, contracts, evidence/claim boundaries,
deterministic validation, and adapters with explicit maturity evidence.

## Recoverable archive requirements

Before any future delete decision, independently verify all of the following:

- GitHub repository identity, archive state, visibility, default branch and
  exact `main` SHA
- every GitHub ref and open PR/issue state
- the local-only `4cee68d` commit and its parent relationship to GitHub main
- a complete Git bundle containing GitHub main, local-only refs and required
  tags
- bundle SHA-256 and `git bundle verify`
- an inventory/manifest of tracked files, Git LFS/submodule state, archive
  contents and excluded local-only data
- the destination and hash of at least one independent recovery copy
- a trial clone or restore that resolves both `bbf212e0` and `4cee68d`
- migration-map entries for every accepted extraction
- confirmation that no active runtime, symlink, process, worktree, task, or
  control-plane record still depends on the repository

No deletion, unarchive, rename, branch removal, local checkout cleanup, or
bundle rewrite is authorized by this audit.

## Recommended retirement sequence

1. Keep `NotVibeDFT` archived and read-only.
2. Review this audit PR and accept/reject each extraction candidate.
3. For accepted candidates, write a current contract first, then port only
   anonymized fixtures or reimplement the narrow behavior.
4. Run the current VibeDFT validation chain and candidate-specific negative
   tests; do not rely on historical test counts.
5. Record exact origin path/commit/blob and destination commit/hash.
6. Re-verify the recovery bundle and perform a trial restore.
7. Update Research-Ops only after actual repository or migration state changes.
8. Ask the user for a separate explicit deletion decision.

## Decision

【推断连接】The next safe action is to review the architecture/audit PR, not to
delete or unarchive `NotVibeDFT`. Phase two may create
`VibeDFT-Official-Sources`; it does not require recovering the old platform.
