# Quantum ESPRESSO release notes — Fixed in version 3.1.1:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `6cc348792809407cca8622e51cac3b4c14ffff5299360cdfb3fd2b7cf56b37a6`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 3.1.1:

  * Methfessel-Paxton broadening was hardcoded in the calculation of
    the electron-phonon coefficients (ngauss1=1 in PH/elphon.f90).
    There is no good reason to use this instead of simple gaussian
    (ngauss1=0), which, moreover, guarantees positive definite results.

                                 * * * * *
```
