# Quantum ESPRESSO release notes — Fixed in version 4.0.1:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `584fff27fef142a06e21e84a3c74a607cfec046c774a1b8a8e70da7e19dcabee`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 4.0.1:

  * Some scripts used in tests/ and in examples were not
    posix-compliant and could fail in some cases
  * In cg calculations with cp, the case of no spin multiplicity
    (i.e. nspin=1) with odd number of bands was yielding an error
    "c second dimension too small"
  * rigid.f90: sum over G-space in long-range term, used in q2r.x 
    and matdyn.x, wasn't really converged for sufficiently large cells
  * too many automatic arrays in "set_asr" called in matdyn.f90,
    causing a mysterious crash for systems larger than a few atoms
  * incorrect call to "sgama" in matdyn.f90 could lead to failures
    with strange messages when calculating phonon DOS
  * c_mkdir is explicitly defined as integer*4 in order to prevent
    problems in 64-bit machines with default 64-bit integers
  * PP/chdens.f90: incorrect orthogonality test for axis
  * GIPAW: 10^3 factor missing in conversion
  * GIPAW: paw_recon[]%paw_betar[] was not initialised and caused NaN's
    with IBM compilers. Courtesy of Christos Gougoussis (IMPMC, Paris).
  * Minor glitches in PWGui
  * cppp.x was not working in v.4.0
  * Workaround for bluegene weirdness extended to complex hamiltonians
  * PP/projwfc.f90: Problems with file names in systems > 1000 atoms
  * Workaround for ATLAS bug causing random crashes
  * Minor bug in helpdoc: adding syntaxFlush to linecard
  * Incorrect dimensions in PW/local.f90 (courtesy of Zhiping)

                                * * * * *
```
