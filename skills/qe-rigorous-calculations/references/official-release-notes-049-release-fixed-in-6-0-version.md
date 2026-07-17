# Quantum ESPRESSO release notes — Fixed in 6.0 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `3c602fad6671eb19801dc0c3979ff8ae068ee340a706faa336d0a6980c4b5fc7`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 6.0 version:

  * TDDFPT, PWCOND, GWW: redirection to /dev/null broke Windows executable
    (commit 12357)
  * PDOS in the non-collinear case was broken by recent changes in indexing 
    (courtesy Mitsuaki Kawamura) (commit (12366)
  * Incorrect format (old version) of the dynamical matrix if ibrav=0 in PHCG
    (commit 12367,12369) and incorrect format if more than 99 atoms
    (commit 12393) (courtesy Shaofeng Wang)
  * disk_io='high' crashing in MD runs (courtesy David Strubbe)
    (commit 12388)
  * Fix for NEB+hybrid functionals (courtesy Davide Colleoni)
    (commit 12391)
  * Incorrect Wyckoff site labels for group #138, origin_choice=2
    (courtesy Marton Voros) (commit 12426)
  * PHonon: support for Goedecker-Hutter-Teter pseudopotentials was missing
    (courtesy of Sebastiano Caravati)
  * turboTDDFPT: Problem if empty states were also computed. 
  * NEB did not recognize its own input if white spaces were present at the
    right of NEB cards (commit 12816)
  * startingwfc='file' with wavefunctions in collected format could yield a 
    bogus "unit not open" error (commit 12913)
  * PW and CP: possible out-of-bound error in TS-vdW due to incorrect 
    allocation of array UtsvdW (commit 12917)
  * EPW: Correct Wannier localization with spinors
  * EPW: Correct Wannier localization with spinors
  * EPW: Electronic velocities in the local approximation now works correctly
    with skipped bands and spin-orbit coupling
```
