# Quantum ESPRESSO release notes — Incompatible changes in 5.1.2 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `4042010e8982c9a2fda7beb6390009b0219346f093bc1ca3551ce96873caffb0`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Incompatible changes in 5.1.2 version:

  * XSpectra: variable ef_r, used to eliminate the occupied states
              from the spectrum, replaced by new variable xe0  
  * PHonon: input variable iverbosity => verbosity
  * The (undocumented) *.evp file of CP uses a slightly different format
    (equally undocumented) since v.5.1.1. In order to use original format,
    compile with __OLD_FORMAT preprocessing variable on.
```
