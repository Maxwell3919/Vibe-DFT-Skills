# Quantum ESPRESSO release notes — Incompatible changes in 5.1.1 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `65dcddb8fbb08c97fcf1dab6a6b31c9942e640049d1543e01ea0b424d21b4af3`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Incompatible changes in 5.1.1 version:

  * Regularization of DFT names for nonlocal functionals:
      "vdw-df3"                   replaced by "vdw-df-obk8"
      "vdw-df4" and "optb86b-vdw" replaced by "vdw-df-ob86"
      "rev-vdw-df2"               replaced by "vdw-df2-b86r"
    Explanation: We have tried to unify the naming convention of the vdW-DF 
    family of functionals built on "Dion et al., PRL 92, 246401 (2004)." 
    Within this family, numbering should be used for different non-local
    pieces of the functionals, such as vdW-DF2. If functionals only change the
    (semi)local contribution, the choice of (semi)local functional should be 
    attached at the end of the name, such as vdW-DF-C09 or vdW-DF-cx.
```
