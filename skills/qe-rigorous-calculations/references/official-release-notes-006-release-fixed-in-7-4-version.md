# Quantum ESPRESSO release notes — Fixed in 7.4 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `01448d16c5dfd932989521c6fc23929a2c7d1eb399d5a5dd0ed7dab2dd037320`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 7.4 version:
  * Stress for USPP and conjugate-gradient algorithm of cp.x was wrong.
    Bug found and fixed by Jeremy Rabone
  * Phonon restart was not working properly in some cases with ultrasoft,
    PPs, due to bad initialization of PP tables - affects v.7.3 and 7.3.1
  * Too small parameter "maxl" in upflib/ylmr2.f90 and upflib/ylmr2_gpu.f90
    for some PAW calculations - affects v.7.3.1 only
  * Since v.7.2 phonon was not working for completely local pseudopotentials 
    such as the VBC pseudopotentials for H. 
```
