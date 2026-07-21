# Gaussian troubleshooting and audit

Preserve the failed input, log, checkpoint identity, environment, and execution record
before changing anything. Diagnose the earliest failed gate and create a new child run;
never overwrite evidence or stack unrelated remedies.

## Contents

1. Triage order
2. Input and checkpoint failures
3. SCF failures
4. Geometry-optimization failures
5. Frequency and thermochemistry failures
6. TD and IRC failures
7. Operational heuristics
8. Failure report

## 1. Triage in gate order

Check in this order:

1. exact input/output/checkpoint identity and Gaussian revision;
2. input section order, charge/multiplicity, atom map, basis/ECP coverage, and units;
3. license/platform/process status and Gaussian termination;
4. SCF or state-solver convergence at the failed geometry;
5. task-specific completion (`Opt`, `Freq`, TD, IRC, utility conversion);
6. numerical convergence and model adequacy;
7. physical interpretation and scientific acceptance.

Stop at the first missing prerequisite. A later “Normal termination” from another job
step or file cannot heal an earlier failure.

## 2. Diagnose input and checkpoint failures

Inspect:

- missing/extra blank lines and keyword-driven input sections;
- route abbreviations or option combinations that resolve ambiguously;
- electron-count/multiplicity conflict and unintended fragment charge/spin;
- atom order changes across QST, constraints, scans, or checkpoint consumers;
- absent element coverage in `Gen`/`GenECP`/ECP input;
- conflicting explicit basis with `ChkBasis`;
- wrong checkpoint role (`Geom`, `Guess`, basis, Hessian, restart, TD vectors);
- stale revision or incompatible geometry/basis/state in a checkpoint;
- an output or child checkpoint that aliases immutable evidence.

Treat “file exists” as inventory only. Require exact hashes and producer metadata.
If the provider rejects input, correct the smallest structural cause in a new file and
re-run the input audit before considering scientific options.

## 3. Diagnose SCF failure before selecting a remedy

First verify the molecular problem: geometry, charge, multiplicity, electron count,
method, basis/ECP, solvent, and intended state. Then inspect the SCF sequence for
oscillation, monotonic slow progress, large density changes, energy jumps, or a state
change. Record the last converged geometry and whether the failure occurs only at one
optimization/IRC point.

Use the official distinctions:

- `SCF=MaxCycle=N` only changes the iteration limit;
- `SCF=QC` uses a slower quadratically convergent procedure and is unavailable for
  restricted open-shell calculations;
- `SCF=XQC` adds QC after conventional SCF fails;
- `SCF=YQC` is documented for difficult very large cases;
- damping, level shifting, Fermi broadening, CDIIS/DIIS, and symmetry controls alter
  the convergence path and can change the converged solution;
- `Guess=Read`, `Guess=Restart`, and `SCF=Restart` have different lineage semantics;
- `Guess=Mix` deliberately breaks alpha/beta and spatial symmetry for candidate UHF
  singlet solutions;
- `Stable` tests a converged HF/DFT determinant; `Stable=Opt` may find a lower solution.

After any remedy, recheck the electronic state, orbital occupations, spin expectation,
stability, energy, forces, and downstream task. SCF convergence to the wrong solution
is a failure, not a success.

First-party anchors: `g16-scf`, `g16-guess`, `g16-stable`.

## 4. Diagnose an incomplete or wrong optimization

Do not respond to every incomplete optimization by increasing `MaxCycles`. Inspect:

- all four provider convergence criteria (maximum/RMS force and displacement);
- energy/force trend, rejected or tiny steps, trust radius, and Hessian updates;
- SCF convergence at every geometry;
- redundant-coordinate, linear-angle, torsion, constraint, or symmetry pathology;
- whether a minimum, TS, or higher saddle was actually requested;
- the Hessian/eigenvalue pattern for a TS search;
- atom order and structural plausibility for QST2/QST3;
- discontinuous electronic-state or solvent behavior.

Use `CalcFC`, `ReadFC`, or `RCFC` only with a documented reason and compatible Hessian
lineage. Change coordinate systems, GIC definitions, constraints, or step size only
after locating the problematic coordinate. Use `Opt=Restart` with the original
optimization intent and immutable parent/child identities. Reapply completion and
frequency gates after every restart.

Treat `Opt=NoEigenTest` and `Opt=Expert` as high-risk expert controls, not routine
fixes; the official Opt page warns about their use. A constrained or scanned structure
cannot support an unconstrained-minimum claim.

First-party anchors: `g16-opt`, `g16-geom`.

## 5. Diagnose frequency or thermochemistry problems

Block interpretation when the geometry is not stationary at the same model chemistry,
the SCF wavefunction is unstable, the derivative calculation is incomplete, or the
mode count is inconsistent with the molecule/constraints.

For negative or near-zero frequencies:

1. inspect the displacement vector rather than its sign alone;
2. separate the intended TS mode from rotations, translations, floppy torsions,
   hindered rotations, constraint artifacts, grid noise, and wrong geometry;
3. tighten the geometry/grid only when the force/displacement evidence motivates it;
4. reoptimize along a meaningful unintended mode when seeking a minimum;
5. repeat the same-model frequency analysis and compare the mode continuously.

For numerical frequencies, audit displacement size, symmetry, per-displacement SCF
convergence, and missing/failed subcalculations. For thermochemistry, record
temperature, pressure, isotope masses, symmetry number, standard state, scaling, and
low-frequency policy. Do not silently replace harmonic modes or publish a corrected
free energy without preserving both raw and derived values.

First-party anchors: `g16-freq`, `g16-vibrational-analysis`,
`g16-thermochemistry`, `g16-stable`.

## 6. Diagnose TD and IRC failures

For TD:

- separate ground-state SCF failure from the excited-state solver;
- verify `NStates`, spin manifold, energy window, basis, and checkpoint compatibility;
- track state character, not only `Root=N`, across geometries;
- flag root flipping, near-degeneracy, large configuration/transition-density changes,
  spin contamination, and an inadequate diffuse/long-range model;
- treat a low/zero oscillator strength as a physical selection-rule result unless
  other evidence shows solver failure.

For IRC:

- verify the starting structure and intended imaginary mode;
- require `RCFC` or `CalcFC` and compatible force-constant lineage;
- record direction/phase, point count, step size, integrator, and both branches;
- distinguish technical path completion from reaching and identifying endpoint basins;
- reoptimize and characterize endpoints independently.

First-party anchors: `g16-td`, `g16-irc`, `g16-scrf`.

## 7. Apply operational heuristics cautiously

The following are **operational heuristics**, not Gaussian defaults, universal remedies,
or native validation:

- Change one causal control at a time and retain parent/child hashes; otherwise the
  reason for recovery is unknowable.
- If SCF error decreases steadily and the state remains correct, a larger iteration
  limit may be reasonable. If it oscillates or jumps, diagnose the guess, state,
  symmetry, near-degeneracy, or algorithm before adding cycles.
- For an optimization that makes steady geometric progress, extend steps via a bound
  restart. For repeated oscillation or negligible progress, examine coordinates,
  Hessian, state continuity, and constraints first.
- For DFT low modes, reproduce with tighter optimization and a consistent grid before
  assigning chemical meaning. Do not use a fixed frequency cutoff as an automatic
  deletion rule.
- For TD geometry work, request more states than the target root alone and audit state
  character at each step; the needed margin is system-dependent and must be converged.
- For IRC endpoints, extend the path only when the trajectory is still descending
  toward a basin; point count alone is not an acceptance criterion.
- Never solve a scientific mismatch by choosing the option that merely produces
  normal termination.

## 8. Emit a failure report

Return:

1. failed stage and earliest failed gate;
2. immutable evidence hashes and revision/environment identity;
3. observed provider messages summarized without licensed-text reproduction;
4. classified cause: input, lineage, environment, SCF/state, task, numerical, or
   interpretation;
5. ruled-out causes and evidence;
6. one smallest next diagnostic or recovery action;
7. whether the action is official behavior or an operational heuristic;
8. required revalidation gates and claim ceiling.

Never delete or overwrite the failed log/checkpoint, conceal a state change, or report
recovery before a fresh complete audit passes.
