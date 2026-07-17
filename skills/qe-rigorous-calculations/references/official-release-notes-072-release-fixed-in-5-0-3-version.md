# Quantum ESPRESSO release notes — Fixed in 5.0.3 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `53b5c88e90017a80d2d506076caada295f80989291ae59b9a82a545bd4143e3c`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 5.0.3 version:

  * PW, PP, PHonon: files for DFT+U produced by previous versions
    could no longer be read
  * PHonon: restart with convt=.true. was not working with PAW
  * PHonon: in matdyn.x, displacement patterns were no longer correct
    if eigenvectors of the dynamical matrix were also written to file
  * PHonon: compatibility with files produced by previous releases
    was broken if pools were used
  * VERY NASTY PHonon bug: symmetry Sq=-q+G introduced in v.5.0.2
    could lead to bad phonons in some cases and has been disabled 
  * PHonon: effective charges eu + PAW were not accurate with pools;
    effective charges eu + US PP + spin-orbit nonmagnetic were not
    working in parallel.
  * Bug fix for NC pseudos with GIPAW info, for upf version 2 only:
    Pseudo local potential was incorrectly written and read. 
  * divide_class: wrong check for T_h
  * PP: incorrect check yielding bogus error in bands.f90 (v.5.0.2 only)
  * CP wasn't working properly with USPP having distinct Q functions 
    for each value of l, due to the never ending l/l+1 problem

                               * * * * *
```
