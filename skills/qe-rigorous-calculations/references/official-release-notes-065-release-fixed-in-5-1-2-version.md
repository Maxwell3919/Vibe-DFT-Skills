# Quantum ESPRESSO release notes — Fixed in 5.1.2 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `6e4bfd9d173cab08a6c96ab4462b7816a48888eb678941c6186663aaaac5f9e1`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 5.1.2 version:

  * Option wf_collect wasn't working with LSDA and one k-point per pool
  * Restarting from interrupted calculations could be spoiled by options
    "startingwfc" and "startingpot": warning added
  * Bug in space-group generator in the monoclinic case.
  * atomic: a small bug was preventing the generation of non-PAW 
    pseudopotentials with GIPAW reconstruction data
  * Changes made in rev.10251 had broken pw.x -pw2casino when just
    one k-point per processor was present. Also: pp converter from upf 
    to casino produced invalid pp for Z>=10 due to insufficient format
  * Symmetry printout could lead to error exit in same cases
  * Restarting from incomplete calculation could lead in some cases
    to mysterious crashes due to usage of unitialized communicator
  * PH: option only_init + US or PAW was not working.
  * Minor printout bug: the printed number of symmetries with fractional
    translations was sometimes incorrect in the non-collinear magnetic case.

                               * * * * * 
```
