# Quantum ESPRESSO release notes — Incompatible changes in 7.5 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `e9e97ce1939522abc682f7d8f8dfc272bb370029d0f87b23d36330e11622cee3`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Incompatible changes in 7.5 version:
  * The Simpson routine for radial integration has been modified for the case
    of an even number of points in the integration grid. The current version 
    is more accurate than the previous one, but may yield slightly different
    numerical results.
```
