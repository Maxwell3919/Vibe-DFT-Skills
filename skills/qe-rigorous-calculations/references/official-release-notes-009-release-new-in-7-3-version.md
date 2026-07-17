# Quantum ESPRESSO release notes — New in 7.3 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `bc018caf781cb8701892edf6b7dbeea8890d8f628c891f48514c34f1d6acc2e3`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
New in 7.3 version:
  * Experimental support for pseudopotentials in PSML format
  * Noncollinear implementation of DFT+U and DFT+U+V in the 
    Dudarev's formulation, including the calculation of Hubbard
    forces, stresses, and Hubbard parameters (L. Binci and N. Marzari, 
    Phys. Rev. B 108, 115157 (2023)). Experimental stage. 
    If J is not specified in the input, then this new implementation 
    is used, otherwise the Liechtenstein implementation is used 
    (see Doc/Hubbard_input for more details).
```
