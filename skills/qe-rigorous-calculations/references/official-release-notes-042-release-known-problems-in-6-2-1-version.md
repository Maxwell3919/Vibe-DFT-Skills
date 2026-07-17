# Quantum ESPRESSO release notes — Known problems in 6.2.1 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `c1ddee43da5f87bcd198c565172afe19c88ffb6ca998567ad0dacea34647e031`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Known problems in 6.2.1 version:

  * pw2bgw.x not working

  * QM-MM not yet working; COUPLE interface not aligned with new parallelism

  * New format for charge density no longer allows to perform a non-scf
    calculation with k-points starting from a scf calculation at Gamma

  * NEB with one k-point per pool requires "wf_collect=.false.", because
    update_neb is not updated for the new format
```
