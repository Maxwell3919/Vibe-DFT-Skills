# Quantum ESPRESSO release notes — Incompatible changes in 6.8 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `1a8140c7b3c70b29c2cd8d62919f09803dd88cb6da9f1da0a0d81e2a1b987223`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Incompatible changes in 6.8 version:
  * lfcpopt & lfcpdyn are replaced by lfcp. Only static optimization of the
    Fermi energy works. Currently, molecular dynamics with FCP does not work.
  * Exchange-correlation code (vdW excepted) moved to XClib/
  * Much more pseudopotential-related code re-organized and moved to upflib/
    Variables ofsbeta ("offset of beta functions") and indv_ijkb0 merged
    Now only ofsbeta is used
  * Code computing [H,x] commutator moved from LR_Modules/ to PW/src/ and
    disentangled from linear-response variables - now is used in PP/ as well
```
