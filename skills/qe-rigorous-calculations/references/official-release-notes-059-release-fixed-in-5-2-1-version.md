# Quantum ESPRESSO release notes — Fixed in 5.2.1 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `2ba1e934d46618826faa8197a9a9f30c855a9185366393b534e32569c5eafa4d`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 5.2.1 version:

  * PW: incorrect calculation of maximum number of plane waves could lead 
    to error exit with hybrid functionals and ultrasoft pseudopotentials
  * PW: cell_dofree = '2Dshape' wasn't working as expected
  * PW: a few do loops included more FFT planes than physical ones in real
    space, leading to inaccuracies in real-space augmentation charge and xdm,
    only if the number of processors nproc_bgrp was not a divisor of nr3
  * XSpectra: v.5.1.2 and 5.2.0 contained a bug in parallelization that could
    lead to incorrect results     
  * TDDFPT: mismatch between actual and expected format of save file
  * Various fixes for compilation on NAG compiler

                               * * * * *
```
