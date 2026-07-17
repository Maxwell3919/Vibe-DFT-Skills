# Quantum ESPRESSO release notes — Fixed in version 2.0:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `c65b643cf408d1d3c9479a278c7a209726b53d2938b99711521875315fae16c7`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 2.0:
  
  * wrong results when running Berry-phase calculation in parallel execution:
    it was not implemented but no warning was issued
  * variable-cell code was subject to overflow and floating-point errors
  * phonon + nosym=.true. was not properly done
  * out-of-bound error in Berry Phase calculation
  * out-of-bound errors in phonon if 4-dimensional irreps were present
    (also d3.x was not working properly in this case)
  * Berry-phase calculation had problems in low-symmetry cases
  * phonon with k-point parallelization (pools) was yielding wrong
    results in some cases (since v. 1.2 included)
  * upftools/cpmd2upf.f90: wrong conversion due to Rydberg-Hartree mess
  * PW/input.f90: lattice parameter a converted to wrong units if input
    is given as a,b,c,cos(ab),cos(ac),cos(bc) instead of celldm(:)
  * Wrong coordinates written if atomic_positions='crystal'
    (thanks to Francois Willaime)

                                 * * * * *
```
