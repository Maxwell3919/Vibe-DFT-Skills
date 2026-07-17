# Quantum ESPRESSO release notes — Fixed in 5.1.1 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `345751ca953f0f4ca33cfd21c479cad4467a779a87030aa06e069317ea224de3`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 5.1.1 version:

  * PWscf: variable-cell glitches at last scf step 
  * PWscf & PHonon: added several checks for unimplemented features
  * PWscf: energy related to external forces wasn't correct
  * CP: Wannier functions dynamics with nspin=2 wasn't working
  * PWscf: restart in variable-cell case wasn't working in v.5.1
  * pot_extrapolation='none' was crashing with a bogus error message
  * PHonon: the recently introduced fix to the G=0 component of the 
    deformation potential at q=0 was not working properly
  * Kernel table for rVV10 nonlocal functional was not written to file,
    breaking restart and postprocessing (no problem for scf)
  * Strange compilation bug on some IBM machines
  * Minor bug plus OpenMP bug in ESM implementation
  * Small bug leading to crashes when restarting some type of constrained
    magnetization calculations (courtesy of Florian Thoele, ETHZ)

                               * * * * *
```
