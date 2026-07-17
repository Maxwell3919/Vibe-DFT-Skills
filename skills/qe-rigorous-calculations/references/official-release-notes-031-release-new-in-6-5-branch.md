# Quantum ESPRESSO release notes — New in 6.5 branch:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `bad997aa4ade7a2c2be3eb5948ae2cc34c82114a5196deeb21a5cfcf997fa66c`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
New in 6.5 branch:
  * For non-local functionals of the vdW-DF and rVV10 families the kernel is
    now calculated on-the-fly rather than read from file. Thus, the kernel
    files vdW_kernel_table and rVV10_kernel_table are no longer needed for
    calculations and the kernel generation programs generate_vdW_kernel_table.x
    and generate_rVV10_kernel_table.x have been removed. The on-the-fly vdW-DF
    kernel calculation does not take long, e.g. ~100 seconds on a single Intel
    Xeon 2.20GHz core and ~12 seconds on 8 cores (Intel 2018 compilers); the
    rVV10 kernel computes in seconds. Detailed information is available in the
    git log commit notes. This work was performed by T. Thonhauser and is
    supported by NSF Grant No. 1712425.
  * turbo_eels code of TDDFPT module now works with ultrasoft pseudopotentials
    and spin-orbit coupling together (Oleksandr Motornyi, Andrea Dal Corso,
    Nathalie Vast). lr_sm1_psi.f90 of LR_Modules is rewritten and simplified.
  * Stochastic-velocity rescaling as a new thermostat for constant-cell MD as
    implemented in dynamics_module (Leonid Kahle, Ngoc Linh Nguyen)
```
