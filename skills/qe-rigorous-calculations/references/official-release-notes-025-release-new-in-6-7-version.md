# Quantum ESPRESSO release notes — New in 6.7 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `bf1ddeadd9861d8b44639af84cecdc869841c87069139abaed45dcfd9d31810e`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
New in 6.7 version:
  * Support for CMake (F. Ficarelli and D. Cesarini, CINECA, with help from
    Ye Luo, P. Delugas, S. Gsaenger)
  * In vc-relax with Hubbard corrections, the final SCF calculation is done by 
    reading atomic occupations from file produced during the vc-relax 
    (rather than recomputing them from scratch).
  * EPW: 
    (1) ZG package to generate special displacements for first-principles non-perturbative calculations 
    at finite temperatures [Marios Zacharias and Feliciano Giustino, Phys. Rev. Research 2, 013357, (2020)].
    (2) Plotting of Fermi surface.
    For the full list of new features, bug fixes, and changes leading to backward incompatibility issues, 
    please visit the Releases page of the EPW documentation site [https://docs.epw-code.org/doc/Releases.html].
```
