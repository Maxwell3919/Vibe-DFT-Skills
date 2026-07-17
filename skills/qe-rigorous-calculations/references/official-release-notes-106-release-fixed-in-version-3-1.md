# Quantum ESPRESSO release notes — Fixed in version 3.1:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `61c3b6e6f35ba141c6dbe1490f27876f44f1fc0db14777c8e88ca91007957aeb`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 3.1:

  * various problems in stress calculation, both in PW and in CP
  * in phonon dispersion calculation, the threshold for diagonalization
    was not always what was expected to be. Minor numerical differences 
    could result.
  * the new algorithm for electron-phonon calculation removes a serious
    bug in the old algorithm, present in v.2.1 to 3 included: when 
    electron-phonon coefficients were calculated together with the 
    dynamical matrix, the symmetrization of coeffcients was incorrect.
    Results from separate calculations were correct.

                                 * * * * *
```
