# Phonon, EPC, and Tc campaign efficiency

Use this reference for conventional phonon-mediated superconductivity campaigns. The target is not merely a finite number: it is a numerically converged Tc within an explicitly declared physical model, solver, Coulomb parameter, and uncertainty budget.

## Keep official capabilities distinct from experience

Official QE behavior supports the following building blocks; verify them against the matching installed version before execution:

- `start_q` and `last_q` split an `ldisp=.true.` calculation over discovered q points.
- `only_init=.true.` performs band and initialization work used by GRID parallelization.
- `recover=.true.` restarts an interrupted `ph.x` run.
- an electron-phonon run with `trans=.false.` can use saved dynamical matrices and deformation potentials with a different, denser electronic k grid.
- `lqdir` stores induced potentials in q-specific directories for electron-phonon work.
- the optimized-tetrahedron EPC route uses a half-step-shifted q grid; with `lshift_q=.true.`, `q2r.x` cannot be used.
- EPW distinguishes coarse electronic/phonon meshes from fine interpolated meshes and can write reusable fine-mesh Eliashberg artifacts. Its mesh-commensurability and restart requirements are version-sensitive.

These are software capabilities, not proof that a particular workflow is scientifically converged or faster on a given machine.

Route execution-time parameter audits through the QE calculation skill and its version-matched official mirror, especially `start_q`/`last_q`, `only_init`, `recover`, `trans`, `lqdir`, `lshift_q`, and `electron_phonon`. For EPW, recheck the current official input documentation before designing fine meshes or artifact reuse.

## What the first anonymized cases establish

The current evidence set supports bounded rules, not universal cost constants:

- In one completed campaign, a q2 screen produced a strong finite-Tc signal while q4 under a denser production protocol reduced the result to nearly zero. Dense-k convergence was good while adjacent-smearing convergence still failed. This is decisive evidence that the q2 result was not production-acceptable, but the protocol change confounds attribution of the reduction to q sampling alone. Therefore q2 is screening evidence, and k convergence cannot substitute for q or smearing convergence.
- Within that q4 campaign, individual irreducible-q response times differed by more than an order of magnitude. Scheduling by q index or equal task count left avoidable critical-path idle time.
- `only_init` timings ranked the later expensive q points usefully in that campaign. This supports a measured scheduling pilot, not yet a universal runtime predictor.
- A separate stopped q4 campaign failed at its first non-Gamma point during diagonalization and later completed that point only after a changed solver path. This independently supports non-Gamma preflight as failure avoidance.
- An apparent q8 campaign contained prepared inputs and a completed electronic seed but no PH result; similarly named running jobs belonged to other working directories. This supports scheduler/output/artifact triangulation.
- Historical accepted projects compare at least two electronic-sampling or PH/Tc curves over a stable overlap interval. Directory labels alone are not the convergence criterion.

Exact material identities, private paths, and unpublished numerical results remain outside this repository. Retain them in authorized private campaign notes.

## Shortest defensible route

The efficient route is a promotion funnel. It does not require every candidate to execute every rung, and it does not define q8 as automatically strict.

The default decision path is `q2 screen -> q4 production baseline -> q6, q8, or EPW only as required by the remaining uncertainty`, not an unconditional `q2 -> q4 -> q8` ladder.

### Declare acceptance before computing

Fix the physical model and record tolerances for at least:

- dynamical stability and treatment of acoustic numerical noise;
- q-grid changes in lambda, omega-log, Tc, and the shape or low-frequency weight of alpha-squared-F;
- electronic k-grid and integration/smearing changes over a common interval;
- Tc solver, temperature mesh, Coulomb parameter or range, and stopping criterion;
- interpolation holdouts if EPW or another surrogate is used;
- absolute Tc tolerance near zero, where relative error is ill-conditioned.

Call the final value `converged within <declared model>` rather than absolutely rigorous.

### Use q2 as a cheap risk screen

Run q2 to find obvious instabilities, gross EPC signals, numerical failures, and candidate ranking. Preserve raw unstable modes and any derived acoustic correction separately.

A positive q2 result can promote a candidate but cannot establish Tc. A negative q2 result can miss a non-high-symmetry anomaly or localized EPC hotspot; reject it only under an explicit screening-risk policy or after independent sentinel q points reduce that risk.

Decide whether the q2 run is disposable or reusable before submission:

- a cheap q2 with reduced response k grid is suitable for broad screening but normally cannot seed production q4/q8 response data;
- a production-compatible q2 costs more but can be reusable if every response-defining input and artifact contract matches later grids.

Do not pay for production-compatible q2 on every low-priority candidate. Promote first, then align protocols for the survivors.

### Converge the cheap electronic axis before expensive q refinement

After reusable dynamical matrices and deformation potentials exist, vary dense electronic k grid and integration/smearing with `trans=.false.` where supported. Compare at least two adjacent dense-k levels over a shared smearing interval containing consecutive valid points, or use the declared alternative integration method with an equivalent convergence test.

Require the needed downstream artifact, not only a normal executable exit. Treat q, k, and smearing gates as orthogonal. If k is stable but the smearing curves do not overlap, the stage is not ready for strict q-grid comparison.

### Build q4 as the first production baseline

Discover the actual irreducible q list and weights from program output. Never hardcode the count. Verify coverage, weights, required dynamical matrices, deformation potentials, and per-q completion.

Run a cheap non-Gamma `only_init` audit for each discovered q before long response jobs. Use measured preflight or prior matched timings to schedule the longest predicted q first across available slots. Store each q by canonical coordinate and protocol identity, not only its grid-local ordinal.

At q4, inspect q-resolved contributions and curve-valued convergence. A finite Tc file or completion marker does not establish acceptance.

### Choose q6, q8, or EPW from the remaining uncertainty

- Choose q6 when a cheaper non-nested check is scientifically valuable. For a two-dimensional in-plane mesh it has fewer full-grid points than q8 and can expose grid-aliasing that a purely nested sequence may hide. It offers less direct data reuse.
- Choose q8 when q4 hotspots, the error budget, or a required nested refinement justify it and the q4 protocol is exactly reusable.
- Choose EPW coarse-to-fine interpolation when explicit fine-q DFPT dominates cost and the system admits a validated Wannier representation. Benchmark it against direct DFPT at withheld q points before trusting fine-grid Tc.
- Stop after q4 or q6 only when every predeclared gate is already satisfied. Continue past q8 if it is not.

When q2-to-q4 changes are large or convergence is nonmonotonic, require an additional independent grid or interpolation holdout. Do not fit an assumed power law through nonsmooth Fermi-surface sampling.

For a single candidate whose q2 screen used a disposable coarse protocol, normally proceed directly to the q4 production baseline after promotion instead of rerunning q2 under the production protocol solely for bookkeeping. Pay for a production-compatible q2 only when its reusable overlap or early stopping value exceeds that extra cost.

### Separate the Tc solver from EPC integration

Reuse accepted alpha-squared-F or EPW fine-mesh artifacts when varying the Coulomb parameter, temperature mesh, or Eliashberg solver controls. Do not recompute DFPT for a solver-only sensitivity study.

Allen-Dynes or McMillan-type estimates and isotropic or anisotropic Eliashberg solutions are different model levels. Report their difference as model sensitivity, not numerical q-grid error.

## Conditional nested-grid reuse

For unshifted uniform grids, q2 points are geometrically contained in q4, and q4 points in q8. The ideal equal-cost full-grid work saved by reusing both earlier stages is

```text
(2^d + 4^d) / (2^d + 4^d + 8^d)
```

where `d` is the number of periodically sampled q dimensions. This ideal is about 24% for a two-dimensional mesh and about 12% for a three-dimensional mesh. It is not an observed wall-time saving: symmetry, q-dependent iterations, queueing, I/O, and failed work change the result.

Reuse an overlapping q point only when all response-defining properties match, including structure, pseudopotentials, cutoffs, charge/spin state, coarse response k grid, occupations, solver tolerances, code compatibility, physical q coordinate, and artifact format. Recompute weights for the target grid.

QE grid-local q ordinals are not stable identifiers across meshes, and a normal `ph.x` restart does not by itself prove safe cross-grid assembly. A future deterministic mapper should canonicalize coordinates, compare protocol hashes, map target-grid weights, verify artifacts, and fail closed on ambiguity. Until that mapper is validated, treat manual cross-grid transplantation as a high-risk pilot rather than routine reuse.

## Scheduling and speculative execution

Represent each irreducible q response as an independently observable task when the code and filesystem layout support it. Record preflight time, response time, cores, restarts, and failure state per q.

Use longest-processing-time-first scheduling only as a campaign-scoped heuristic until repeated data validate the predictor. Compare its counterfactual makespan with the actual dependency schedule, but label the result estimated unless both schedules were measured under comparable conditions.

Speculative next-rung work is allowed only when it consumes otherwise idle authorized resources, cannot corrupt reusable state, passes safety preflights, and remains hard-gated from scientific acceptance until the prior rung promotes it. Cancellation cost and wasted core-hours belong in the campaign record.

## EPW branch

EPW can replace explicit fine-q DFPT with Wannier interpolation, but it adds its own gates:

- coarse k/q convergence and complete deformation-potential inputs;
- Wannier disentanglement/localization quality and band interpolation near the Fermi level;
- direct-DFPT holdout checks for frequencies and electron-phonon matrix elements or derived q contributions;
- fine k/q commensurability, Fermi-window, smearing, delta-function, and temperature-grid convergence;
- isotropic versus anisotropic solver choice and reusable artifact completeness;
- memory, storage, pool/image parallelization, and restart benchmarking on the actual machine.

Do not claim EPW is cheaper until a matched pilot includes Wannierization, preprocessing, interpolation, solver, failed attempts, storage, and human setup time. Once validated, reuse written fine-mesh artifacts for solver-only scans instead of repeating electron-phonon interpolation.

## Optimized-tetrahedron branch

Treat optimized tetrahedron EPC as an independent integration branch. Its shifted q grid can reduce reliance on Gaussian-smearing scans, but it conflicts with the simple unshifted q2/q4/q8 reuse path and with `q2r.x` under `lshift_q=.true.`. Plan separate phonon-dispersion/IFC evidence and compare against the smearing route under a common observable gate.

Do not switch integration methods mid-sequence and interpret the difference as q-grid convergence.

## Promotion and stopping logic

The decision engine should behave conservatively:

```text
q2 screen
  -> reject only under an explicit false-negative risk policy
  -> otherwise promote selected candidates

reusable q response available
  -> converge dense k plus adjacent integration settings
  -> fail closed if required artifacts or curve overlap are missing

q4 production baseline
  -> accept only if all declared gates pass
  -> choose q6 for a cheaper independent check
  -> choose q8 for justified nested refinement
  -> choose EPW when fine-q DFPT cost dominates and interpolation is validated

final Tc
  -> report numerical, interpolation, solver, and model uncertainties separately
```

Near-zero Tc requires an absolute stopping tolerance and supporting lambda/omega-log or spectral evidence. A relative-Tc-only gate is unstable there.

Acceptance requires, at minimum, two adjacent q levels stable under the declared absolute-plus-relative observable tolerances, two adjacent dense-k levels stable over a common integration interval, complete q weights/artifacts, physical phonons, and a fixed Tc model/solver protocol. Add a third q level or direct interpolation holdout after a large or nonmonotonic change. The grid labels themselves are never the gate.

## Tooling implied by the cases

Add deterministic tools only after their inputs and failure modes are stable. The first useful tools are:

- a read-only campaign inventory that reconciles scheduler workdir, output state, artifacts, and dependencies;
- a q-discovery and canonical-coordinate mapper with protocol hashes and weight checks;
- a curve comparator for q/k/smearing levels using overlap intervals and absolute-plus-relative tolerances;
- a per-q cost collector and slot-aware schedule simulator;
- a promotion report that keeps measured facts, counterfactual estimates, and scientific gates separate.

These tools should emit machine-readable evidence, while the human-readable case remains free-form.
