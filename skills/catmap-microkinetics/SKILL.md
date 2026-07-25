---
name: catmap-microkinetics
description: Plan and audit CatMAP 0.4.1 microkinetic evidence with explicit reaction networks, stoichiometry and site balances, energy and rate units, thermochemistry provenance, coverage and steady-state convergence, sensitivity robustness, uncertainty coverage, and strict limits on mechanistic claims; use without executing untrusted .mkm, log, pickle, or Python artifacts.
---

# CatMAP Microkinetics

Read [the local official-manual cache route](references/manual-cache-route.md) before using any external official document body.

This is a **development, non-routable Skill**. It validates a safe declarative JSON interchange and original synthetic fixtures. It does not import CatMAP, execute a setup file, accept a native log/pickle, run a solver, or establish a catalytic mechanism.

## Start here

1. Read [official-sources-and-version-strategy.md](references/official-sources-and-version-strategy.md) and [version-matrix.yaml](references/version-matrix.yaml) before relying on a version string, behavior, or default.
2. Read [modeling-and-validation.md](references/modeling-and-validation.md) for reaction notation,
   thermochemistry, descriptor/scaler/solver/mapper behavior, labeled outputs, stiffness,
   sensitivity, and acceptance checks. It separates official behavior from operational heuristics.
3. Use [calling-and-recipes.md](references/calling-and-recipes.md), [software-capability-catalog.json](references/software-capability-catalog.json), and [task-recipes.json](references/task-recipes.json) for documented Python/CLI calls, inputs, outputs, and failure semantics.
4. Use `scripts/catmap_catalog.py` to search calls, emit a non-executing documentation plan, or probe metadata without importing CatMAP. A plan never authorizes execution.
5. Read [fail-closed-contract.md](references/fail-closed-contract.md), choose one task from [task-evidence-profiles.json](references/task-evidence-profiles.json), then use `scripts/catmap_guard.py` only on the declarative JSON interchange.
6. Resolve stable codes through [finding-catalog.json](references/finding-catalog.json) and task/provider maturity through [maturity-matrix.json](references/maturity-matrix.json).
7. Treat [weak-model-decision-table.json](references/weak-model-decision-table.json) as the only machine routing source: evaluate ascending priority, select the first match, and use its evidence-free final default when no earlier case is established.
8. Check [environment-license-boundary.md](references/environment-license-boundary.md) before proposing an actual environment. Never execute an untrusted `.mkm`, `.log`, Python, or pickle artifact.

## Candidate task matrix

| Task | Required evidence | Current maturity | Maximum candidate claim |
|---|---|---|---|
| `network-audit` | Species, elemental composition, site occupancy, elementary stoichiometry | synthetic-validated | no positive claim |
| `thermochemistry-audit` | Balanced network plus common units/reference, conditions, species free energies, barriers/corrections and provenance | synthetic-validated | no positive claim |
| `steady-state-audit` | Hash-bound network/thermochemistry plus solver identity, residual, multiple initial states, coverages, site closure, finite rates and rate normalization | synthetic-validated | no positive claim |
| `sensitivity-audit` | Passing steady state plus explicit perturbation method/scales, parameter IDs, convergence fraction and coefficients | synthetic-validated | no positive claim |
| `uncertainty-audit` | Passing steady state plus distribution provenance, sample accounting, convergence fraction and ordered intervals | synthetic-validated | no positive claim |
| `microkinetic-package-audit` | All of the above in one immutable package | synthetic-validated | no positive claim |

Electrochemistry, coverage-dependent interactions, transient kinetics, transport coupling, multiple site lattices with non-unit occupancy, and descriptor-map interpolation are `design-only` until they receive independent contracts and fixtures. Software capability is not adapter maturity.

## Non-negotiable gates

Keep these states independent:

- **provider gate**: exact CatMAP 0.4.1 tag/revision, Python environment, dependency lock, GPL obligations, and execution record;
- **input-safety gate**: declarative JSON only; reject executable `.mkm`, `.log`, `.py`, `.pkl`, and `.pickle` inputs;
- **lineage gate**: network, thermochemistry, and result content hashes agree with the model record;
- **network gate**: unique species/reaction IDs, all referenced species defined, elemental balance, site balance, and declared reversibility;
- **unit/reference gate**: energy, temperature, pressure, coverage, rate basis, standard state, and thermodynamic reference are explicit;
- **thermochemistry gate**: complete species energies, correction provenance, condition identity, non-negative forward/reverse barriers, and barrier-cycle consistency;
- **solver gate**: solver name/settings/branch, convergence flag, iteration count, finite residual and predeclared tolerance, plus at least the predeclared number of initial states whose stored final-coverages/fingerprints agree within tolerance;
- **coverage gate**: finite coverages within tolerance, declared empty-site species, and site totals close to capacity;
- **rate gate**: finite elementary/net rates with explicit units, declared active-site normalization, and consistent species production residuals;
- **sensitivity gate**: method, parameter/output selectors, at least two declared perturbation scales, sign convention, and convergence at each perturbation;
- **uncertainty gate**: distribution/provenance, deterministic sampling identity, requested and converged sample counts, and ordered quantiles;
- **data-partition gate**: disjoint calibration/evaluation IDs, zero overlap accounting, declared purpose, and a recomputed partition hash;
- **claim gate**: technical results remain distinct from mechanism identification, rate-determining-step assignment, extrapolative catalyst ranking, or experiment agreement.

Process exit zero, a CatMAP object that loads, solver `converged=true`, a small residual, plausible coverages, smooth volcano plots, and scientific acceptance are different observations.

## Deterministic CLIs

Search the versioned software/manual catalog or generate a documentation-only plan:

```bash
python3 -B skills/catmap-microkinetics/scripts/catmap_catalog.py search "rate control"
python3 -B skills/catmap-microkinetics/scripts/catmap_catalog.py plan recipe.run-mkm-model
python3 -B skills/catmap-microkinetics/scripts/catmap_catalog.py probe
```

`plan` never executes or authorizes CatMAP. Interaction and electrochemistry recipes are `feature-only` and return exit `3`. On 2026-07-19 the local probe found no CatMAP executable, distribution, or module, so native validation remains `native-not-run`.

The guard uses the Python standard library only. It performs bounded strict JSON parsing, rejects duplicate keys and non-finite numbers, and refuses outputs that alias any input. Request and evidence reads share one retained root directory descriptor; relative components use no-follow `openat` traversal and special files are rejected without blocking. Sorted reports use a same-directory fsynced staging descriptor plus atomic hardlink create-if-absent publication with post-publication inode, size, link-count, and payload verification. Every existing target and the compatibility `--overwrite` flag are rejected. It has no external executor.

```bash
python3 skills/catmap-microkinetics/scripts/catmap_guard.py plan \
  --request skills/catmap-microkinetics/examples/plan-request.json \
  --output catmap-plan-report.json

python3 skills/catmap-microkinetics/scripts/catmap_guard.py audit \
  --request skills/catmap-microkinetics/fixtures/audit-request-pass.json \
  --output catmap-audit-report.json
```

Stable exit codes:

| Code | Meaning |
|---:|---|
| `0` | Selected deterministic synthetic plan/audit passed |
| `2` | Unsafe, privacy-bearing, malformed, duplicate-key, non-finite, or contract-invalid input |
| `3` | Provider integration, real-artifact maturity, unsupported scientific mode, or expert evidence is missing |
| `4` | A declared safe JSON artifact cannot be parsed under the selected candidate contract |
| `5` | A network, thermochemistry, solver, coverage, rate, sensitivity, uncertainty, or lineage gate failed |

Reports contain no timestamps or resolved paths, so identical evidence produces identical semantic output.

## Scientific interpretation boundary

- Stoichiometric balance is necessary but does not prove that the reaction network is complete or physically correct.
- A common energy reference is necessary; it does not validate the DFT method, scaling relation, transition-state search, entropy model, electrochemical convention, or lateral-interaction approximation.
- Agreement among a finite predeclared set of initial states is useful branch evidence, but a converged mean-field steady state can still be one of multiple mathematical solutions and does not establish global uniqueness, kinetic stability, or experimental relevance.
- Degree-of-rate-control or finite-difference sensitivity is local to model, state, perturbation, parameterization, and solver branch. It is not automatically a unique rate-determining step.
- An uncertainty interval is meaningful only for the declared parameter distributions and correlations and a leakage-free evaluation partition; it is not total model-form uncertainty.
- No automatic result may claim the true mechanism, catalyst ranking outside the validated domain, experiment agreement, or causal design rule. Future automated output is capped at `eligible_for_expert_review`; acceptance requires an independent human decision.

## Handoffs

On promotion, consume reviewed `reaction-network-manifest@1.0` and `thermochemistry-dataset@1.0`; produce `microkinetic-model-manifest@1.0`, `normalized-dataset@1.0`, and `artifact-manifest@1.0`. These interfaces remain planned, so this candidate emits only a local validation report and must not expose a shared route.

`dft-postprocess` may later plot normalized results, but it cannot repair network, unit, solver, or claim gates. `dft-campaign-efficiency` may compare measured solver cost only after scientific gates are preserved.

## Activation blockers

- exact CatMAP v0.4.1 source revision and dependency lock tested in an isolated Python 3.10 or 3.11 environment;
- reviewed safe exporter from trusted CatMAP objects to the declarative JSON interchange, without loading untrusted native artifacts;
- real first-party tutorial forward fixtures and adversarial native-file cases with lawful redistribution and exact hashes;
- shared schemas for the three planned microkinetic interfaces and cross-interface semantic validation;
- validated coverage, steady-state, sensitivity, uncertainty, interactions, electrochemistry, and multi-site profiles separately;
- executor records that separate process, solver, numerical, task, and scientific state;
- full repository regression, two-round weak-model blind evaluation, and explicit atomic promotion review.

Fixture origin and exclusions are in [fixture-manifest.json](references/fixture-manifest.json).
