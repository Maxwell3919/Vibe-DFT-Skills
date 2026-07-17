# Quantum ESPRESSO release notes — Incompatible changes in 5.0 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `387dee622e773ebe478cc919b3a857b9cd0de90e65a9a6c8c50f39e5c3b38e60`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Incompatible changes in 5.0 version:

  * Postprocessing codes dos.x, bands.x, projwfc.x, now use
    namelist &dos, &bands, &projwfc respectively, instead of &inputpp
  * Directory reorganization: whole packages into subdirectories,
    almost nothing is in the same directory where it used to be. 
  * atomic masses in the code are in amu unless otherwise stated
  * Options 'cubic'/'hexagonal' to CELL_PARAMETERS removed: it is no 
    longer useful, the code will anyway find the correct sym.ops.
  * Options 'bohr'/'angstrom'/'alat' to CELL_PARAMETERS implemented
  * -DEXX no longer required for exact exchange or hybrid functionals
  * PHonon: input variable 'elph' replaced by 'electron_phonon'
```
