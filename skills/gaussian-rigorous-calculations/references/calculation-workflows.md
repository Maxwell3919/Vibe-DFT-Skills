# Gaussian calculation workflows

Use exactly one workflow as the primary path, then add only explicitly justified
stages. These workflows describe public Gaussian 16 capabilities; only the narrow
synthetic `SP/Opt/Freq/Opt+Freq` subset is implemented by `gaussian_guard.py`.

## Contents

1. Shared evidence gates
2. Single-point energy and properties
3. Minimum optimization and relaxed scans
4. Frequency and thermochemistry
5. Transition structures
6. IRC connectivity
7. TD vertical excitations
8. TD excited-state structures and spectra
9. Solvent-state discipline
10. Checkpoint-derived analysis

## 1. Apply shared evidence gates

Before every workflow, freeze:

- molecular structure identity, atom order, charge, and multiplicity;
- Gaussian product/revision and licensed environment;
- full method/basis/ECP/grid/solvent model chemistry;
- task options, checkpoint roles, resources, and additional input sections;
- target observable, units, tolerance, and comparison protocol;
- immutable per-stage input/output/checkpoint identities.

After every workflow, distinguish process exit, Gaussian termination, SCF/state
convergence, task completion, numerical convergence, physical validity, and scientific
acceptance. A normal termination satisfies only the technical-termination gate.

## 2. Plan a single-point calculation

Use a single point to evaluate the selected electronic state at one fixed geometry.
Do not imply that the geometry is stationary or appropriate for the selected method.

Require:

1. an explicit model chemistry rather than the empty-route default;
2. a geometry lineage and any geometry-method mismatch recorded as a limitation;
3. a converged SCF or method-specific correlation solver;
4. the correct method-specific final energy, not simply the last number in the log;
5. wavefunction stability/spin diagnostics where the method and state require them;
6. an observable-specific basis, grid, solvent, and integration convergence study.

For energy differences, keep charge/state definitions, grids, solvation conventions,
thermal corrections, and reference geometries comparable. Never mix electronic energy,
enthalpy, and Gibbs free energy without naming every added correction.

First-party anchors: `g16-sp`, `g16-scf`, `g16-stable`, `g16-dft`.

## 3. Optimize a minimum or perform a relaxed scan

For a minimum candidate, specify `Opt` and record the coordinate system, constraints,
initial Hessian policy, convergence policy, and maximum steps. Treat “Optimization
completed” as a local stationary-point candidate only.

Require a same-model frequency calculation before identifying the stationary-point
type. Search relevant conformers/protonation states/spin states separately; one
successful optimization cannot establish a global minimum.

For a relaxed scan, bind every `ModRedundant ... S nsteps stepsize` or GIC definition,
atom index, sign/unit convention, point count, and per-point optimization status.
Treat a scan as path exploration, not a minimum-energy path or transition-state proof.

Use `Opt=Tight`/`VeryTight`, grids, `CalcFC`/`ReadFC`, GIC, Cartesian, or step controls
only after connecting the choice to a diagnosed problem. Record constrained degrees of
freedom and exclude them from an unconstrained-minimum claim.

First-party anchors: `g16-opt`, `g16-geom`, `g16-dft`.

## 4. Compute frequencies and thermochemistry

Run frequencies at a stationary point using the same method, basis, frozen-core
choice, grid, solvent model, and geometry definition used for the optimization. The
public Freq page explicitly warns that a different-level optimized geometry makes the
frequency transformation invalid.

Audit:

- analytic versus numerical derivative route and completion;
- expected vibrational mode count for an ordinary unconstrained isolated molecule
  (`3N-6` nonlinear, `3N-5` linear), with constrained, periodic, fragment, or other
  special models handled by their own profile;
- every negative and near-zero mode, its eigenvector, and whether a constraint or
  numerical grid explains it;
- IR/Raman/VCD/ROA options and method availability;
- temperature, pressure, isotopic masses, symmetry number, and standard-state
  convention for thermochemistry;
- frequency scaling and low-frequency treatment as external scientific choices.

`Freq=ReadFC` reuses an existing Hessian for a new analysis; it does not repair a bad
geometry or create new force constants. Bind the original Hessian, geometry, masses,
and model chemistry. Do not claim thermochemical accuracy from harmonic output alone.

First-party anchors: `g16-freq`, `g16-vibrational-analysis`,
`g16-thermochemistry`, `g16-stable`.

## 5. Locate and validate a transition structure

Choose one documented starting route:

- `Opt=TS` from a justified near-TS structure;
- `Opt=QST2` from reactant and product structures;
- `Opt=QST3` from reactant, product, and an initial TS structure.

For QST2/QST3, require identical atom identity and order in every molecule
specification. Use an initial Hessian strategy appropriate to the route and retain the
curvature test unless an expert explicitly accepts the risk. Do not treat
`NoEigenTest` as a generic convergence fix.

After optimization, require exactly one chemically intended imaginary mode, inspect
its displacement, and verify that it describes the proposed coordinate. Then follow
both IRC directions and identify the endpoint structures independently. One imaginary
frequency without mode and endpoint evidence is not a transition-state assignment.

First-party anchors: `g16-opt`, `g16-freq`, `g16-irc`.

## 6. Establish IRC connectivity

Start from a frequency-verified transition-structure geometry. Provide initial force
constants using `IRC=RCFC` from the exact checkpoint or `IRC=CalcFC`; the official page
requires an initial Hessian. Record `Forward`/`Reverse` or the default two-direction
path, `Phase`, `MaxPoints`, `StepSize`, integrator, coordinate system, and convergence
settings.

Require:

1. technical completion for each direction;
2. a monotonic, continuous path audit rather than only the final table;
3. sufficient path length to enter the endpoint basins;
4. independent endpoint optimizations and frequency/state checks;
5. state and model-chemistry continuity along the path.

Do not equate “forward” with products without a declared `Phase`; the provider defines
direction from the transition-vector phase. Do not infer a reaction network, rate, or
mechanism from one IRC path alone.

First-party anchor: `g16-irc`.

## 7. Plan TD vertical excitations

For TD-HF/TD-DFT, declare the reference ground-state wavefunction, singlet/triplet
manifold, `NStates`, any energy window, and the `Root` only when a state-specific
property is requested. The public TD page documents excitation energy, oscillator
strength, spin expectation, symmetry, and leading configurations in output; none alone
is a complete state identity.

Audit at least:

- ground-state SCF convergence and, where applicable, stability;
- enough requested states to cover the energy window with a margin;
- basis diffuseness and functional suitability for valence, Rydberg, or charge-transfer
  character;
- state character using configurations, transition density/orbitals or other declared
  diagnostics, not state number alone;
- oscillator-strength, symmetry, and spin selection rules without treating a dark
  state as a failed calculation;
- solvent equilibrium/non-equilibrium convention and the target experimental process.

Converge the number of states and model chemistry for the observable. A lower root
index after a geometry or model change need not represent the same physical state.

First-party anchors: `g16-td`, `g16-scrf`, `g16-dft`.

## 8. Optimize or analyze an excited state

For `TD=(Root=N,NStates=M) Opt`, bind the intended state character before the first
step and audit it at every geometry. Treat root flipping, near-degeneracy, symmetry
change, and large character changes as blocking findings. Never accept a completed
geometry optimization based only on an unchanged root number.

For an excited-state frequency calculation, require the same state, method, basis,
grid, solvent convention, and optimized geometry, plus stable state tracking and the
expected mode analysis. The G16 release notes and TD page document analytic TD
gradients/frequencies for supported method/functionals; verify method availability for
the selected revision rather than generalizing that statement.

For absorption/emission or vibronic comparisons, keep vertical, adiabatic, zero-point,
and solvent-relaxation contributions distinct. Record whether the geometry and solvent
are ground-state, excited-state equilibrium, or non-equilibrium.

First-party anchors: `g16-td`, `g16-freq`, `g16-release-notes`, `g16-scrf`.

## 9. Keep solvent-state conventions explicit

Record the SCRF model, solvent, cavity/radii, and any `Read` parameters. The public
SCRF page documents non-equilibrium solvation as appropriate for rapid vertical
excitations and equilibrium solvation as the default for TD/CIS excited-state geometry
optimizations. Verify the actual requested options; do not infer them from a solvent
name in prose.

For solvation free energies, bind matching gas/solution structures and thermal/standard
state conventions. Provider documentation of SMD as a model choice does not establish
adequacy for a specific solute, solvent, charge state, or reaction.

First-party anchor: `g16-scrf`.

## 10. Hand off checkpoint-derived analysis

Convert a checkpoint only after the producer run passes its applicable technical
gates. Bind `.chk -> .fchk -> derived artifact` hashes and the exact density/state,
orbital, grid, and unit selectors. Before a Multiwfn handoff, prefer an explicitly
documented wavefunction-bearing format and record whether the requested analysis
requires orbitals, density matrices, basis metadata, or derivatives absent from the
chosen export.

Do not use visualization, population analysis, or a converted file to repair an
unconverged SCF, wrong state, invalid stationary point, or broken checkpoint lineage.

First-party anchors: `g16-formchk`, `g16-cubegen`.
