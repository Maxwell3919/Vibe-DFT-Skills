# Quantum ESPRESSO release notes — Fixed in version 4.2:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `b75e7725f746ae4a6ebc5d690e75aff0e29e2cab166fb3d826bb967cfda2ac53`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 4.2:

  * A few occurrences of uninitialized variables and of incorrect INTENT
  * The value of DFT set in input (instead of DFT read from PP files) was
    ignored by all codes using the data file (phonon, postprocessing, etc)
  * PW: glitches in restart (now it works also with exact exchange)
  * D3: real-space contribution to the Ewald term was incorrect, since the
    initial release. Since such term is usually very small, the error was 
    also very small. Also: preconditioning was not properly implemented,
    causing unnecessary slow convergence
```
