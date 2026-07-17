# Quantum ESPRESSO release notes — Incompatible changes in 5.4 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `099ca3ccc81869a2e1660f3974810e17f0e56635d9298ff2446607aaab02d1d5`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Incompatible changes in 5.4 version:

  * Directories PW/tests/ and CPV/tests/ deleted, superseded by "testcode"
    tests in test-suite/
  * k+G indices "igk" no longer written to and read from file (PW only, 
    will be extended to all codes)
  * Matrix inversion routines merged into "invmat" in module matrix_inversion
  * Module "gvecw", in Modules/gvecw.f90, includes previous CP module "gvecw"
    and several PW variables taken out from module "wvfct":
    qcutz, ecfixed, q2sigm, ecutwfc
    New variable gcutw=ecutwfc/tpiba2 used also in PW every time "gk_sort"
    is called - gcutw is initialized at startup or when data files are read
  * Common modules for linear-response codes moved to new directory LR_Modules/
  * Routines for subspace diagonalization moved to LAXlib/
  * flib/ directory deleted, routines in flib/ moved to Modules/

                               * * * * *
```
