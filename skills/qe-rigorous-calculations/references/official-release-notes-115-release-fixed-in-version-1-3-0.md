# Quantum ESPRESSO release notes — Fixed in version 1.3.0:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `35fd223de7ed8564e54fc5857e79e590a3ea1f46b6f4d2dcb354df332d74021c`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 1.3.0:

  * PH/elphon.f90 : el-ph calculation in the US case was not correctly
    working in v.1.2.0 (it was not implemented in previous versions).
    An US term in the calculation of deltaV * psi_v was missing.
    Fixed by M. Wierzbowska and SdG
  * various problems caused by too short file names fixed:
    file and directory names up to 80 characters are allowed
    (thanks to Serguei Patchkovskii and others) 
  * LAPACK routines DSYTRF and DYSTRI require some character arguments
    (like 'U', 'L'). While most LAPACK implementations accept both
    lowercase and uppercase arguments, the standard is uppercase only.
    Various anomalies in self-consistency were caused by lowercase
    arguments.
  * Incorrect Make.pc_abs fixed
  * PGI compiler v.3.3-2 on Linux: PP/chdens.x coredump fixed
  * various T3E glitches in v.1.2.0 fixed
  * PP/work_functions.f90 : STM maps did not work in version 1.2.0
    (undefined variable lscf was used, call to sum_band no longer needed)
  * PP/projwave.f90: symmetrization of projected dos was incorrectly 
    performed using d1,d2,or d3 instead of their transponse.
    (affects all previous versions)
  * PW/new_ns.f90: symmetrization of occupation matrix ns needed for LDA+U
    calculations used incorrectly d2 matrices instead of their transponse. 
    Thanks to Lixin He for finding out the problem and the solution.
    (affects all previous versions)
  
                                 * * * * *
```
