# Quantum ESPRESSO release notes — Fixed in v.7.2:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `88cf3d635e01a1d63a66e700ea83246d5caaefc957c76a38ac10c8137b0b2e7e`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in v.7.2:
  * Mysterious MPI errors in "custom" parallel diagonalization, produced
    on some MPI libraries by destruction of nonexistent communicators
  * v.7.1 of CP for GPU was not working for pseudopotentials with nonlinear 
    core correction
  * in v.7.0 and 7.1 of pw.x the calculation of forces under a macroscopic
    electric field in parallel execution was crashing due to a misspell
  * pw.x was not able to read J0 using the new Hubbard input syntax,
    and it was not printing the correct manifolds in the output when
    two Hubbard channels per atomic type are used
  * hp.x was not checking the compatibility of the q-mesh and FFT mesh
  * ppacf.x was not working any longer in parallel in v7.1 
  * neb.x was unable to read the HUBBARD card from input since v7.1
  * r2r4 coefficient for Ba in DFT-D3 was incorrect since the original
    release in v.6.2.1 (noticed by Valid Askarpour)
  * Fully-relativistic PPs generated with QE versions 6.7 to 7.1 may contain
    an incorrect "PP_AEWFC_rel" tag instead of the correct one "PP_AEWFC_REL" 
    (noticed by Andrea Dal Corso)
  * Non-magnetic spin-orbit calculations could in some rare case produce
    NaN's in the energy (noticed by Andrea Dal Corso)
  * CP wasn't honoring "exx_fraction" in v.7.1  (fixed by Hsin-Yu Ko)
  * QEHeat and KCW were not working if compiled for GPU
  * SCF failure to converge wasn't always exiting with a non-zero code since
    v7.0 (fixed by A. Fonari)
```
