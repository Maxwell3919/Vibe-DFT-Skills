# VibeDFT readiness audit — 2026-07-28

Review base: `main@74774932935d3bc15bfd4b6ab0545f9457880beb`

## Decision

The repository is suitable as a **policy, documentation, deterministic-audit, and evidence-contract layer** for VibeDFT. It is not yet suitable as the complete VibeDFT runtime for unattended multi-host DFT campaigns.

The current active surface can support structure inspection, calculation planning, conservative input/output auditing, bounded convergence checks, postprocessing checks, cost evidence, and provenance-shaped handoffs. The central operational routes required by the intended Talos-to-cluster workflow remain development-only dry runs:

- scheduler submission, observation, retry, cancellation, and remote file staging;
- cross-stage workflow orchestration and execution authorization;
- structure generation/export as an operational route;
- scientific acceptance, reporting, and review-response routing;
- native `ph.x`/EPW execution and real-artifact validation for two-dimensional superconductivity.

This is a capability boundary, not a documentation defect. The repository should remain usable in its present audit role while the execution layer is built separately and connected through the existing contracts.

## Evidence boundary

This audit inspected the current registries, policies, active and development Skills, route validator, promotion validator, test runner, CI workflow, synthetic QE two-dimensional EPC bundle, dependency declaration, and recent merged PR history.

No QE, VASP, CP2K, SIESTA, scheduler, SSH transport, remote filesystem, or cluster was executed. No claim is made that the current test suite passes on a fresh checkout. The GitHub connector returned no pull-request-associated workflow run for the reviewed head, so current CI success was not independently established.

## Suitability by VibeDFT function

| Function | Current state | VibeDFT suitability |
|---|---|---|
| Official-document provenance and version-aware lookup | Strong, content-addressed local-cache design with explicit gaps | Suitable |
| Structure inspection and manifest production | Active deterministic route | Suitable with representative-model limits |
| QE/VASP/CP2K/SIESTA input and output audit | Active, conservative code-specific routes | Suitable for supported parser surfaces |
| Numerical convergence bookkeeping | Active bounded analyzers | Suitable when the observable, tolerance, protocol, and raw evidence are bound |
| Native DFT execution | No active executable adapter | Not suitable |
| Scheduler and remote execution | Development dry-run only; no scheduler/transport adapter | Not suitable |
| Cross-stage orchestration | Development read-only audit only | Not suitable |
| Two-dimensional phonon/EPC/Tc validation | Synthetic repository fixture; QE Skill treats `ph.x` and EPW surfaces as manual/not automated | Partially suitable for validator development only |
| Scientific acceptance | Routed to a development/non-routable Skill | Not suitable |
| Multi-host state and provenance | Contracts exist; no active durable process engine or event store | Not suitable |
| Human-readable reporting and review response | Development routes | Not suitable as an automated terminal route |

## P0 findings

### P0-1 — Active lifecycle is not closed over retained activation evidence

`docs/lifecycle-promotion-policy.md` requires every development-to-active transition to reference an immutable activation record and requires historical records to remain retained. The current `skill-registry` schema accepts no activation-record or maturity-catalog reference for active entries and requires their `activation_requirements` arrays to be empty. The canonical registry snapshot also does not include an activation or maturity ledger.

A two-phase promotion validator exists and correctly validates synthetic commit-bound promotion evidence under `evidence/promotions/<skill-id>`. However, current active entries are not canonically bound to retained promotion artifacts. Earlier repository work introduced conservative activation and maturity ledgers for inherited active Skills; those canonical paths are absent at the reviewed head.

**Failure mode:** an active route can remain active after its evidence is removed, becomes stale, or is no longer reachable from the canonical registry snapshot.

**Required correction:**

1. add immutable `activation_record` and `task_maturity_catalog` references to every active Skill entry, or restore equivalent canonical ledgers;
2. include those records in `RegistrySnapshot` and repository-wide audits;
3. hash-check each referenced record and its evidence graph;
4. reinstate a conservative `legacy-active-review-required` state for inherited Skills lacking independently reviewed promotion evidence;
5. cap such routes at `documented_behavior_only` until route-specific real-artifact evidence is restored.

### P0-2 — Terminal intents resolve to non-executable routes

The frozen response policy maps scheduler submission/control to `dft-hpc-execution`, execution authorization/scientific acceptance to `dft-project-orchestrator`, and structure/report/review/literature terminal intents to other development Skills. The route validator simultaneously requires development routes to be non-routable and to declare no executable actions.

**Failure mode:** a weak model can return a registered Skill ID for a terminal intent even though that Skill is intentionally non-executable. The registry is internally lifecycle-consistent but operationally misleading.

**Required correction:**

- require every non-null terminal-intent target to be `lifecycle: active` and `routable: true`;
- map unavailable terminal intents to `null` plus a stable blocked reason until promotion;
- add a mutation test proving that a development target cannot enter the canonical terminal-intent map.

### Phase A1 implementation note

Phase A1 adds `registry/active-evidence.yaml` to the canonical registry snapshot.
The repository history contains no retained, independently reviewed,
commit-bound promotion bundle for any of the seven inherited active Skills, so
all seven are recorded as `legacy-unclosed`; no reviewer, review time,
historical test result, or promotion commit is reconstructed. Each record binds
the current source-tree identity and a separate route/task evidence reference.
This status prohibits claims that independent activation review or lifecycle
evidence closure is complete, but it does not demote the Skill or lower an
existing action/task maturity ceiling.

The route validator now enforces that every non-null terminal target is active,
routable, has a reachable action, and satisfies the terminal intent's explicit
capability binding. Scheduler submit/control require the corresponding side
effect on a reachable action; a route-level capability declaration is not
sufficient. Structure, reporting, review-response, and literature intents bind
the target Skill kind and produced interface. Scheduler and other missing
operation routes remain `null`; execution authorization and scientific
acceptance are classified as human boundaries, while external publication and
destructive deletion are intentionally disabled.

`tools/vibedft_readiness.py` reports activation-evidence readiness,
operational readiness, and automation coverage separately. Human boundaries
and intentionally disabled intents are excluded from the automatable-intent
denominator, so they do not permanently block aggregate readiness. Execution
authorization remains a human boundary because an Agent may prepare or check
an execution request, but the authority to approve its side effects is not
delegated by route availability.

### P0-3 — Current CI no longer exposes all declared trust boundaries

The current workflow runs on one Ubuntu/Python 3.12 job, executes the main and development tests plus Skill validation, and builds the active-only artifact only for tags. Earlier merged trust-boundary work explicitly described Python 3.11–3.13, Ubuntu/macOS smoke coverage, history privacy scanning, activation/maturity ledger checks, semantic-obligation audits, and active-only distribution checks. Several of those surfaces are no longer explicit in the current workflow and two former ledger paths are absent.

The main test runner does call the repository audit, which reduces the gap, but the workflow does not make each high-risk boundary independently visible or artifacted.

**Required correction:** split CI into independently reported jobs:

1. registry/contracts/promotion evidence;
2. active and development Skill tests;
3. privacy and restricted-content history scan;
4. active-only distribution reproducibility and verification;
5. Python-version matrix;
6. at least one non-Linux portability smoke test;
7. official-source cache check when materialized.

Pin third-party GitHub Actions by immutable commit SHA in the release workflow.

### P0-4 — The primary scientific route is not a real VibeDFT route

The active QE Skill automates a conservative allowlisted `pw.x` core. It explicitly classifies `ph.x`, `neb.x`, and other advanced executable surfaces as `not automated`. The QE two-dimensional EPC golden bundle is synthetic and contains no native QE output, material, or superconducting prediction.

For the current research program, `pw.x → ph.x → q2r.x/matdyn.x → EPW` is a core route rather than an optional extension. The repository already defines many correct scientific gates, but it does not execute or validate that native chain end to end.

**Required correction:** create a development route dedicated to QE two-dimensional phonon/EPC/superconductivity with explicit stage contracts and a legally reusable real-artifact fixture. Promotion requires, at minimum:

- exact QE and EPW build identities;
- SCF/NSCF/phonon/EPC parent-lineage closure;
- pseudopotential-set identity and hashes;
- two-dimensional electrostatics and boundary-condition declaration;
- cutoff, vacuum, smearing, electronic `k`, phonon `q`, and fine EPW mesh convergence against named observables;
- direct treatment of imaginary modes, the flexural acoustic branch, ASR, and two-dimensional LO-TO behavior;
- `alpha2F(omega)`, q/mode-resolved lambda, total lambda, and `omega_log` closure;
- explicit `mu*`, Allen–Dynes/Migdal–Eliashberg model identity, and claim ceiling;
- restart, partial-q, and failure fixtures;
- independent review using a second parser or independent recomputation of the decisive derived quantities.

### P0-5 — Reproducible installation is under-specified

The repository has `requirements-dev.txt` with a mixture of exact and open lower bounds, but no `pyproject.toml`, package metadata, supported Python declaration, dependency lock, or stable installed CLI entry points. The Skills refer to repository-relative scripts and symlink installation.

**Failure mode:** the same commit can resolve materially different parser and numerical-library versions, and external agents must infer repository layout rather than consume a versioned runtime API.

**Required correction:** package deterministic tooling as a versioned Python distribution, declare supported Python versions and optional dependency groups, generate a reviewed lock for CI/release environments, and expose stable console entry points. Keep the portable Skill directories consumable without requiring the entire developer environment.

## P1 architecture decision

VibeDFT should use this repository as the **scientific policy and contract plane**, not as the sole process engine.

Recommended layer ownership:

1. **Skills and policy plane — this repository**
   Human/agent instructions, claim ceilings, scientific gates, schemas, route declarations, official-source receipts, synthetic fixtures, and promotion evidence.

2. **Runtime plane — versioned Python package**
   Route resolution, contract validation, action envelopes, authorization/lease enforcement, idempotency keys, process state, retries, cancellation, and plugin discovery.

3. **Code adapters**
   QE, VASP, CP2K, and SIESTA input generation, native invocation, output parsing, restart detection, and code-specific error classification. Each adapter owns supported-version ranges and real-artifact tests.

4. **Transport and scheduler adapters**
   Local, SSH, Slurm, PBS, and future backends. Site profiles remain outside the public Skill source and contain no credentials.

5. **Durable provenance/state store**
   Immutable inputs, outputs, events, hashes, decisions, leases, environment identity, and parent-child relationships. Conversation memory and Git are not runtime databases.

6. **Scientific validators**
   Observable-specific convergence, dimensionality, model validity, cross-code checks, and publication-claim boundaries. These remain independent of scheduler success.

## Reuse instead of reimplementation

Two established workflow-engine families cover much of the missing runtime surface:

- **AiiDA** provides remote-computer execution, scheduler and transport plugins, checkpointed workflows, and a provenance graph. It is the stronger fit for the intended Talos-controlled, multi-server, long-running campaign model.
- **jobflow/jobflow-remote** provides a lighter Python Job/Flow composition model and dynamic workflows. It is easier to embed but requires a deliberate provenance and remote-operations design.
- **custodian-style handlers** provide a useful pattern for application-specific error detection and bounded recovery. Recovery policies must remain subordinate to VibeDFT scientific gates and explicit authorization.

Do not fork or duplicate a complete HPC workflow engine inside the Skill repository. Implement a narrow VibeDFT adapter pilot against one engine, then retain or replace it based on measured operational behavior.

## Engineering sequence

### Phase 0 — Restore the trust boundary

- close P0-1, P0-2, and P0-3;
- publish a generated capability/readiness report from canonical registries;
- mark all legacy active routes with evidence-backed claim ceilings;
- establish a release tag whose active-only artifact is reproducibly verified.

**Exit:** no active route or terminal intent can exist without hash-closed evidence and an executable route.

### Phase 1 — Runtime MVP on one QE host

- package the runtime and contract validators;
- implement one local or SSH transport and one Slurm adapter;
- implement immutable attempt creation, submit, observe, cancel, and terminal-event capture;
- invoke only a narrow QE `pw.x` SCF/relax route;
- retain human authorization and fail-closed unknown-state handling.

**Exit:** a restartable QE pilot produces a complete, queryable provenance chain without relying on conversation state.

### Phase 2 — Two-dimensional superconductivity route

- implement the staged QE/DFPT/EPW adapter and scientific validators in P0-4;
- add real-artifact fixtures and independent derived-quantity recomputation;
- separate technical completion, numerical convergence, physical validity, and scientific acceptance.

**Exit:** one small public two-dimensional reference system can be reproduced end to end under a pinned protocol, with all limitations explicit.

### Phase 3 — Multi-host campaign operation

- add site-profile abstraction for Maxwell, Preston, hzw, and bcgong without committing private identities;
- add transfer manifests, resource observations, retries, recovery, and cancellation audits;
- make Talos an orchestrator client of the runtime rather than the sole holder of campaign state.

**Exit:** the same workflow can move between approved profiles without changing the scientific plan or losing provenance.

### Phase 4 — Cross-code validation

- add CP2K/SIESTA/VASP native adapters only for routes backed by real fixtures;
- implement structure, energy/force, and selected observable comparison contracts;
- keep code disagreement as evidence rather than forcing normalization.

## Immediate acceptance checklist

The next integration PR should not claim VibeDFT runtime readiness until all items below pass:

- [ ] every active Skill has a hash-verified immutable activation and maturity record;
- [ ] every non-null terminal intent targets an active, routable route;
- [ ] CI exposes registry, promotion, privacy, distribution, portability, and source-cache gates separately;
- [ ] deterministic tooling is packaged and dependency-resolved reproducibly;
- [ ] one native QE route is executed through an authorized runtime adapter with durable provenance;
- [ ] the two-dimensional EPC route has at least one real-artifact fixture and an independent derived-quantity check;
- [ ] no scheduler success or parser success can raise a scientific claim ceiling by itself.

## Final scope judgment

Keep and strengthen the existing contracts, official-source pipeline, fail-closed parser behavior, workspace attempt identity, claim ceilings, and separation of execution from scientific acceptance. Avoid further expansion of planned software identities until the runtime and one primary QE scientific route are operationally closed.

The next repository milestone should be **one narrow, real, reproducible VibeDFT execution path**, not broader documentation coverage or additional placeholder Skills.
