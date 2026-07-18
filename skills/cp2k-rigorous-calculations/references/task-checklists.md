# CP2K task evidence checklists

Use only the relevant checklist. Passing the generic auditor does not satisfy these items.

## Static energy and forces

- Verify basis-set family/quality and pseudopotential identities for every `KIND`.
- Converge `CUTOFF`, `REL_CUTOFF`, k-point sampling, SCF tolerance, cell/vacuum controls, and basis quality against the claimed observable.
- Check charge, multiplicity/UKS state, XC/corrections, periodicity, Poisson solver, and force/stress requests.
- Confirm finite energy/force/stress evidence and stable electronic state.

## GEO_OPT and CELL_OPT

- Verify optimization completion and final force/stress criteria rather than normal program termination alone.
- Check constraints, optimizer, step limits, cell degrees of freedom, and restart ancestry.
- Recompute the final structure with a controlled static calculation when the downstream observable requires it.
- Separate ionic optimization convergence from numerical basis/grid/k-point convergence.

## Molecular dynamics

- Verify ensemble, thermostat/barostat, timestep, masses, constraints, seed, equilibration, production window, and restart continuity.
- Inspect conserved quantities or target-distribution diagnostics appropriate to the ensemble.
- Establish sampling sufficiency and uncertainty for the claimed time-averaged observable.
- Do not infer trajectory validity from a final timing table.

## Bands and DOS/PDOS

- Bind the result to a verified parent density/wavefunction and identical Hamiltonian settings.
- Record k path/mesh, labels, spin/SOC conventions, number of states, occupations, smearing/broadening, projections, and energy reference.
- Check band/DOS dimensions, projection closure, Fermi/reference alignment, and state continuity.

## Vibrational analysis and phonons

- Verify displacement/finite-difference controls, force accuracy, symmetry, supercell or molecular boundary conditions, and every required child calculation.
- Report imaginary modes with sign and convention; do not hide them in plots.
- Converge forces, displacement size, supercell/q sampling, interpolation, and non-analytic corrections when relevant.

## BAND/NEB

- Inventory every image and replica, endpoints, atom mapping, spring/optimizer settings, per-image energies and forces, and restart lineage.
- Verify force convergence for all images and independently validate the saddle region.
- Do not infer a barrier from only the primary output or a partial image set.

## Hybrid, DFT+U, dispersion, k-points, and advanced methods

- Resolve every decisive method-specific keyword in the matching manual.
- Converge method-specific cutoffs, auxiliary basis/ADMM controls, exact-exchange screening, unoccupied states, grids, and finite-size effects as applicable.
- Validate the intended electronic/localization state and compare only identical model definitions.
