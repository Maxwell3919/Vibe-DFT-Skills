# Quantum ESPRESSO release notes — New in 6.8 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `43f20f08a5ea53b5d37130a8b891de4d4ccd264ec434fd4ead69aa24190cb4eb`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
New in 6.8 version:
  * Grand-Canonical SCF (J. Chem. Phys. 146, 114101 (2017)) for constant-mu
    method is implemented by S. Nishihara and S. Hagiwara. [arXiv:2012.10090]
  * Calculation of spin-current matrix elements (Phys. Rev. B 99, 235113) 
    for spin Hall conductivity using Wannier interpolation, in pw2wannier.x
    (Minsu Ghim, Seoul National U.)
  * GWL iterative Www method from JCTC 15 (6) 3710, 2019: Joshua Elliot 
    (U. Manchester), N. Colonna, M. Marsili, N. Marzari, P. Umari
  * Many-Body Dispersion (MBD) correction: Szabolcs Goger (U. Luxembourg),
    Hsin-Yu Ko (Cornell), et al.
  * Support for GPU via CUDA Fortran brought to the main repository
  * Calculation of DORI and of ELF for nspin=2 (Dong Yang, Qin Liu, JSG)
  * Interface for BerkeleyGW extended to hybrid and meta-GGA functionals:
    Fangzhou Zhao (Berkeley)
  * Implementation of the turboMagnon code in TDDFPT [EPJB 91, 249 (2018)]
    (T. Gorni, O. Baseggio, I. Timrov, P. Delugas, S. Baroni)
  * EPW: 
    (1) Hall mobility and Hall factor.
    (2) Isotropic linearized Eliashberg equation to get Tc
    For the full list of new features, bug fixes, and changes leading to backward incompatibility issues, 
    please visit the Releases page of the EPW documentation site [https://docs.epw-code.org/doc/Releases.html].
```
