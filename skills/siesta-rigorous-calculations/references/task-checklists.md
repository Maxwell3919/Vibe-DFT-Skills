# SIESTA task evidence checklists

Read only the requested section. These are evidence requirements, not universal parameter values. Machine-readable automation/maturity boundaries live in `task-evidence-profiles.json`.

## SCF and single point

- Structure/species/pseudopotentials, charge/spin and competing electronic states.
- Basis composition/confinement, `Mesh.Cutoff`, eggbox sensitivity, k sampling or molecular Gamma justification.
- XC/model, occupations/temperature, solution method, SCF criteria/mixing/iteration limit and restart ancestry.
- Unique version/run boundaries, exact input echo, failure/warning precedence, final energy convention, forces/stress if used.
- Observable-specific convergence and independent physical/model checks.

## Fixed-cell and variable-cell relaxation

- All electronic checks at every relevant geometry, explicit method, degrees of freedom, constraints, `MD.Steps`, and force/stress targets.
- `GeometryMustConverge=true`, final relaxed/unrelaxed marker, final structure identity, maximum force vector norm, state continuity and restart lineage.
- For variable cell: target stress/pressure, cell degrees of freedom, Pulay/basis/grid stress, volume/shape stability, and production-static recalculation. This remains manual.
- Re-evaluate the final structure with the production electronic protocol when required by the claim.

## Molecular dynamics

- Ensemble, thermostat/barostat variables, time step, starting velocities/temperature, conserved quantity, and boundary conditions.
- Equilibration exclusion, drift, autocorrelation/effective samples, production length, statistical uncertainty and replica strategy.
- Restart continuity for positions, velocities, cell, thermostat/barostat and electronic state.
- A parser-readable completion/energy trace does not validate an MD ensemble or observable.

## Bands

- Bundle-verified human-accepted SCF parent density/Hamiltonian and identical structure/state/version/protocol.
- Band path, reciprocal convention, symmetry labels, discontinuities, spin/SOC channels and energy reference.
- Basis/mesh, parent sampling, path resolution, unoccupied window and avoided-crossing robustness.
- Exact producer/consumer files and versions for bands/postprocessing.

## DOS, PDOS and LDOS

- Accepted parent, DOS/PDOS/LDOS k-grid family, energy grid/window, broadening, energy zero and spin/channel convention.
- Projection orbital mapping, normalization, completeness/leakage and integrated-state checks.
- Required eigenvalue/wavefunction/Hamiltonian artifacts and exact lineage.
- Converge k sampling, energy resolution, broadening, empty states and projection/basis behavior against the claimed feature.

## Phonons and vibrations

- Bundle-verified human-accepted force-converged parent, displacement method/amplitude, supercell/molecule treatment and symmetry.
- Identical basis/mesh/k-grid/pseudopotentials/SCF/state for all displacements; demonstrate force noise below signal.
- Mass/isotope, mode normalization, acoustic/translational rules and imaginary-mode diagnosis.
- Converge displacement, supercell/q sampling, electronic force accuracy and non-analytic treatment where relevant.

## Optical response

- Accepted ground-state parent, polarization/tensor convention, gauge/approximation and energy reference.
- Empty-state count/window, optical k mesh, frequency grid and broadening.
- Sum-rule/static-limit/causality checks as applicable, plus k/empty-state/grid convergence.

## RT-TDDFT

- Accepted ground-state/wavefunction lineage, perturbation/field definition, time step/integrator and propagation length.
- Norm, charge and energy drift; absorbing/boundary treatment; restart continuity.
- Windowing, Fourier resolution, damping/broadening and spectral-range limitations.

## TranSIESTA and TBtrans

- Separately bundle-verified human-accepted electrodes/device with compatible species, pseudopotentials, basis, mesh, Hamiltonian conventions and transverse sampling.
- Electrode-device geometry mapping, screening, chemical potentials/bias, temperature, charge and NEGF contour convergence.
- Exact TSHS/TSDE/electrode Hamiltonian roles and producer/consumer versions.
- Independently converge electrodes, device SCF, transverse k points, contour/energy sampling and transport-model dimensions.

## Generic or unsupported features

Define a feature-specific profile, official version evidence, required inputs/outputs, failure markers, parent roles, observable extraction and negative tests before claiming automation. Until then, report `documented/manual review only`.
