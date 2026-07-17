# Quantum ESPRESSO release notes — Fixed in version 4.1.1:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `a2818371571eeec705e5655b83aa8ebc6ccf2c40283140bd9f815528603fedd2`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 4.1.1:

  * newly added DFT-D wasn't working properly with k-point parallelization
  * Gamma-only phonon code wasn't working any longer if pseudopotentials
    with nonlinear core correction were used
  * Check of lspinorb flag consistency between left/right lead and
    scattering region in pwcond.x was not working properly; wrong
    print-out of E-Ef when Nchannels=0 also fixed.
  * Check on convergence of variable-cell damped dynamics was not
    working as expected in the presence of constraints
  * Velocity rescaling in CP was not working, and it was performed
    also if not required when ion velocities were set to 'random'
  * ESPRESSO_TMPDIR is caught by gipaw.x as well
  * Phonon calculation could not be performed with only local PPs
  * Small error in the definition of the saw-tooth potential for slab
    calculations with E-field: the "physical" dimensions of the R-space
    grid are nr1,nr2,nr3 NOT nrx1,nrx2,nrx3
  * Misc compilation problem for: gfortran v.4.1 (casino2upf),
    pathscale 3.2 (mp_base),  xlf 12.1 (buggy compilation of iotk)
  * Possible memory leak in PW/update_pot.f90
  * Spin-polarized calculations in CP had a bug since v.4.1  when using
    parallel distributed diagonalization ("ortho" group)
  * FFT glitches: Nec SX routines were not properly called,
    OpenMP was not compatible with all FFTs
  * augmentation charges in real space (tqr=.true.) and k-point
    parallelization (pools) was not working due to bogus check
  * fhi2upf.x : fixed segmentation fault in some cases with ifort
  * OLYP XC functional was incorrectly flagged as Meta-GGA 
    (courtesy of Latevi Max Lawson Daku)
  * Minor corrections and extensions to the documentation

                                * * * * *
```
