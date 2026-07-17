# Quantum ESPRESSO release notes — Incompatible changes in 5.3.0 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `cd3305d1d49ae3e48c447bec6aa83ee5d75b8fdffa55d18f151fb3362f1d4dda`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Incompatible changes in 5.3.0 version:

  * Standard F2003 calls to: get_environment_variable, get_command_argument, 
    command_argument_count, flush, are used everywhere instead of wrappers.
    Some old compilers may no longer work and must be considered unsupported.
  * Old Fermi Surface plotting tools kvecs_FS.f, bands_FS.f90, in PW/tools/,
    replaced by new code PP/src/fermisurface.f90
  * Reshuffling of FFT-related modules: 
    "gather_*"  and "scatter_*" routines moved from module fft_base 
                                                 to module scatter_mod
  * All FFT-related code moved to FFTxlib/
  * Linear algebra parallelization made independent of its parent communicator
    by introducing variable ortho_parent_comm, addressing the whole group.
    In PW ortho_comm is now a sub-communicator of intra_pool_comm and nolonger
    of intra_bgrp_comm.

                               * * * * *
```
