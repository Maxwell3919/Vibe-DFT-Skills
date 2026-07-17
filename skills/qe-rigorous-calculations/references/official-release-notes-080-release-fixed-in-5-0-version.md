# Quantum ESPRESSO release notes — Fixed in 5.0 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `4a2df0c7946159bb352c5711a4abf161fe5aadd777284ec85bbd79c4ee8c4e01`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 5.0 version:

  * Missing checks for unimplemented cases with electric fields
  * CP with electric fields wasn't working any longer in parallel
    due to an unallocated variable
  * VERY NASTY bug: exchange-correlation keyword 'PW91' was incorrectly 
    interpreted (PZ LDA instead of PW) in all 4.3.x versions
  * A few glitches when the standard input is copied to file
  * PW: LDA+U crash in the final step of a vc-relax run, due to a
    premature deallocation of a variable
  * PW: constraint 'atomic direction' on non-collinear magnetization
    wasn't working properly
  * PW: tetrahedra were not working with magnetic symmetries, 
    and not yet working in the non-collinear case as well.
  * Velocity rescaling in variable-cell MD wasn't really working
  * Workaround for frequent crashes in PAW with vc-relax
  * In some cases spin-polarized HSE was yielding NaN's
  * Two instances of an array not always allocated passed as variable to
    routine (init_start_k and dynmatrix.f90) - harmless but not nice
  * disk_io='low' or 'none' wasn't working if a wavefunction file from a
    previous run was found
  * CP + OpenMP without MPI wasn't working with ultrasoft pseudopotentials
  * Bug in CASINO to UPF converter
  * Bug in k-point generation in the non-collinear case
  * ESM with spin polarization fixed
  * Weird problem with irreps in PHonon
  * Bug in turbo_lanczos.x . Restarts of polarizations other than ipol=1 
    or ipol=4 were not working properly due to buggy test_restart routine.

                               * * * * *
```
