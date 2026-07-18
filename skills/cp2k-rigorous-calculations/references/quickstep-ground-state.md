# Quickstep ground-state evidence

Read this file for GPW/GAPW energy, force, stress, relaxation parent, band/DOS parent, or molecular-dynamics force evaluations.

## Resolve the decisive sources

At minimum resolve `dft`, `qs`, `mgrid`, `scf`, `xc`, `poisson`, `cell`, `kind`, `basis-methods`, `pseudopotential-methods`, and the relevant task page. Add `kpoints`, `scf-ot`, `scf-diagonalization`, `scf-smear`, `outer-scf`, `hfx`, `admm`, `dft-plus-u`, `vdw-potential`, or `sccs` when present.

## Keep independent convergence dimensions

Do not collapse these into a single cutoff study:

1. Gaussian basis family and quality for every `KIND`;
2. pseudopotential/all-electron model and valence definition;
3. GPW/GAPW choice and associated grid controls;
4. `CUTOFF`, `REL_CUTOFF`, grid count and smoothing choices;
5. SCF target, solver, preconditioner/mixing, occupation and added-state policy;
6. k-point sampling or finite cell/vacuum size;
7. XC, hybrid, Hubbard, dispersion, solvent and electrostatic model;
8. charge, multiplicity, UKS/ROKS and electronic-state continuity;
9. restart/wavefunction ancestry;
10. the actual claimed energy, force, stress, gap, density or response observable.

## Input evidence gate

Require explicit, version-resolved evidence for:

- one supported Quickstep force evaluator;
- cell/coordinate/topology identity and periodicity;
- every `KIND`, basis label and potential label;
- every external data filename and supplied SHA-256;
- charge/spin policy and XC model;
- MGRID and SCF controls used for production;
- k-point or Gamma-only policy;
- restart policy and parent hash when reused.

Do not infer a scientifically suitable basis or potential from a recognized name.

## Run evidence gate

Require coherent start/end/version/run-type markers, zero unresolved warnings, no fatal/non-finite markers, all required SCF cycles converged, finite primary observables, and task-specific completion/evidence roles. A final total energy is not proof of force, stress, state, or property validity.

## State continuity

Across convergence points compare charge, multiplicity, spin moment/state label, occupations/smearing, orbital solver, restart origin, cell/geometry policy and method flags. A lower numerical energy in a changed state is not a convergence point in the original series.
