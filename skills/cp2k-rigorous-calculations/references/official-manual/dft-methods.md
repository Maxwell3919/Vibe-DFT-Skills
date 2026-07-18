# CP2K official manual snapshot: dft-methods

- Source: https://manual.cp2k.org/cp2k-2026_2-branch/methods/dft/index.html
- Raw SHA-256: 4e8db05ef1fa7ef41f476bbb7fe0a38b4feee025566d787e1770fb664788d559
- Status: version-matched cached official text; reopen the source for current live verification.

Density Functional Theory



Gaussian Plane Wave

Gaussian Augmented Plane Waves

Hartree-Fock Exchange

HFX with ADMM

HFX-RI for Γ-Point (non-periodic)

HFX-RI with k-Points

Basis Sets

Pseudopotentials

K-Points

How to make a SCF run converge

How to Converge the CUTOFF and REL_CUTOFF

Local Resolution of Identity

Constrained DFT

Constrained Nuclear-Electronic Orbital DFT

Linear Scaling DFT

GauXC

Density functional theory in CP2K is primarily provided by the Quickstep module. Most production

calculations use the Gaussian and plane waves (GPW) method with Gaussian basis sets,

pseudopotentials, and real-space grids for densities and potentials. The Gaussian augmented plane

waves (GAPW) method extends the same framework to all-electron and more core-sensitive calculations.

For new inputs, first choose a consistent basis-set and potential pair, then converge the MGRID

cutoffs and the SCF settings for the target property. The pages in this section collect the main

Quickstep ingredients: GPW/GAPW, hybrid functionals and ADMM, local RI, constraints, k-points, basis

sets, pseudopotentials, and grid convergence.

References



Kühne2020

Iannuzzi2026
