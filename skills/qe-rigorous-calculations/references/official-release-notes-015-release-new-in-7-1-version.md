# Quantum ESPRESSO release notes — New in 7.1 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `5a5376429a65de99d54ad1d4586fecf469b5d35fd638ca713763ba45c5723e63`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
New in 7.1 version:
  * DFT+RISM (1D, 3D, Laue) by S. Nishihara & M. Otani [Phys. Rev. B 96, 115429 (2017)].
  * Improved, streamlined and extended porting to NVidia GPUs
  * KCW package for Koopmans-compliant functionals in a Wannier representation:
    https://journals.aps.org/prx/abstract/10.1103/PhysRevX.8.021051.
    Developed and maintained by N. Colonna, R. de Gennaro, E. Linscott
  * If no explicit parallelization options -nk, -nt, -nd are provided,
    pw.x will figure out suitable values for optimal, or at least, not
    too bad, parallelization
  * EPW v.5.5. For the full list of new features, bug fixes, and changes leading
    to backward incompatibility issues, please visit the Releases page of the 
    EPW documentation site [https://docs.epw-code.org/doc/Releases.html].
```
