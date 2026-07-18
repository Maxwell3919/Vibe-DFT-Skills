# CP2K advanced methods and sampling

Use this file to identify additional evidence; it does not grant automated support.

## Hybrid/HFX and ADMM

Resolve `hfx`, `hfx-screening`, `hartree-fock-methods`, and `admm`/`admm-methods` as applicable. Record exact exchange definition, range separation/truncation, screening, periodic treatment, auxiliary basis identities, ADMM method, k-point support, memory/distribution controls and restart policy. Converge method-specific screening, auxiliary basis and finite-size dimensions against the claimed observable.

## DFT+U and dispersion

Resolve `dft-plus-u` and `vdw-potential`. Record affected `KIND`/angular channels, complete U/J parameterization and occupation/localization state. For dispersion, record model/library, reference functional, damping/parameters and periodic contribution policy. Never compare calculations with different corrections as one numerical series.

## Post-Hartree-Fock and excited states

For MP2/RPA/GW, TDDFPT, XAS, real-time propagation or transport, route to `wf-correlation`, `gw-methods`, `tddfpt`, `xas`, `real-time-propagation`, or `transport`. Require method-specific occupied/unoccupied spaces, auxiliary bases, frequency/grid controls, finite-size/k-point treatment, solver convergence and parent-state binding. These surfaces remain `official-routed` or `design-only` until dedicated forward fixtures exist.

## Solvation, fields and charged systems

Resolve `sccs`, `poisson`, `cell`, and any field/dipole section. Record boundary dimensionality, Poisson solver, cell/vacuum, net charge, neutralization/correction convention, dielectric/cavity parameters and reference potential. Normal termination does not establish a meaningful charged-cell energy, work function or solvation energy.

## QM/MM and force-field methods

Resolve `qmmm` and the exact MM/FIST sections. Inventory topology, force-field parameters, link atoms, QM/MM partition, electrostatic coupling, periodicity and long-range treatment. The bundled auditor does not validate this surface and must block a positive technical profile.

## Enhanced and quantum sampling

For metadynamics, path integrals, i-PI, Monte Carlo or Ehrenfest dynamics, resolve the matching sampling method page and all input sections. Record collective variables, bias history, replica/bead inventory, thermostats, exchange/coupling, timestep, seeds, equilibration and estimator uncertainty. These workflows require dedicated task profiles before automated acceptance.

## Capability/build gate

Do not assume a compiled feature is present because the manual documents it. Bind the audited output version, source revision/build flags and linked-library evidence to features such as LibXC, DFTD4, ELPA, GPU accelerators, SMEAGOL, SIRIUS or machine-learning runtimes.
