# Quantum ESPRESSO release notes — Fixed in 7.5 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `553e8f53d624aa3929eb028f8852770fadab4c87df1db007c12a200eb7ba7374`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 7.5 version:
  * Problem with too short variable holding tag name when reading UPF files,
    occurring only for some fully-relativistic pseudopotentials
  * Warning on poor testing of Berry Phase calculation removed, thanks to
    accurate testing performed by Riccardo Dal Molin and Antimo Marrazzo.
  * Symmetrization glitches on many processors (reported by Yunqi Shao)
  * Crash for noncolinear PAW case on many processors (reported by I. Timrov)
  * The HP code for the magnetic noncollinear case had a bug
    when symmetry was used (some symmetry arrays were not re-initialized
    when perturbing Hubbard atoms) and the magnetization direction flip was 
    missing in the Hubbard term (for the second Sternheimer equation) (fixed by L. Binci)
```
