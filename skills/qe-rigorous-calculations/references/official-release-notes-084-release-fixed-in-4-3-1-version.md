# Quantum ESPRESSO release notes — Fixed in 4.3.1 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `7a18fd0aaed41b1fd6331544fd5898cb294be177ec8bc91b29789c1402b2365f`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 4.3.1 version:

  * atomic: behavior of which_augfun='PSQ' made consistent with documentation
  * CP: LDA+U buggy; PLUMED wasn't working
  * Misc compilation and configure problems: line exceeding 132 characters, 
    syntax not accepted by some compilers, pathscale+mpif90 not recognized, 
    etc.
  * PW: nasty out-of-bound bug leading to mysterious crashes or 
    incorrect results in some variable-cell calculations. Also in
    variable-cell: last scf step could crash due to insufficient
    FFT grid if the final cell was larger than the initial one
  * PW: minor bug in damped dynamics (hessian matrix incorrectly reset)
  * PW: bug in LDA+U forces for the Gamma-only case
  * Electron-Phonon code wasn't working any longer in serial execution
  * PH with input variable "fildrho" and D3 were not working due to 
    inconsistencies in the calls to io_pattern
  * PWCOND: fixed bug when the write/read option is used for the case 
    of different leads. 
  * NEB + nonlocal exchange (DF-vdW) or hybrid functionals wasn't working
  * NEB: incorrect parsing of intermediate images fixed
  * HSE numerical problems in function expint
  * XSPECTRA wasn't working any longer due to missing updates to
    read_file_xspectra.f90
  * epsilon.f90: the term 1 must be added to diagonal components only! 

                               * * * * *
```
