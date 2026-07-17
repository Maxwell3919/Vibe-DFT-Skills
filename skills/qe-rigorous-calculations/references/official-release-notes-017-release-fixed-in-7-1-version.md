# Quantum ESPRESSO release notes — Fixed in 7.1 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `1712837b6bf0440cb000d60e0bcd5c5debe58486982813ae4fd5ba6fb9b500de`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 7.1 version:
  * Berry phases could in some cases be off by a factor eR/V.
    Present since v.6.6 (noticed by S. Spreafico, fixed by R. Cohen)
  * `divide_class_so` routine could yield the wrong irreducible representations
    classification in the D3_h  group (G.J. Ferreira, A. Dal Corso) 
  * XSPECTRA gave incorrect results with k-point parallelization, since
    at least v. 6.6, due to missing broadcast of recomputed Fermi energy
    (found and fixed by Fanchan Meng, Brookhaven)
  * Bugfix in DFPT+U with PAW pseudos and when fildvscf/=''
  * Makov-Payne correction wasn't working with ibrav=0 and cubic cell (A. Fonari)
  * Card ADDITIONAL_KPOINTS wasn't working as expected (Prasenjit Ghosh)
  * Subtle bug in G-vector ordering, usually triggered by almost-but-not-quite
    symmetric primitive lattice vectors, was affecting k=0 calculations (not CP)
    since v.6.0. The ultimate fix would require to change routine hpsort_eps; 
    the current workaround consists in not recomputing k+G indices if k=0.
  * In CMake GPU builds, one routine fftx_threed2oned_gpu was not compiled with
    a proper GPU compiler option and caused failure in GGA-noncolin calculations.
  * CP with Hubbard U was crashing also when reading the xml file (v.7.0)
  * Bugfix in turboMagnon for k point grids that have Gamma or points at the
    Brillouin zone edge (the weights were not correct)
  * Libxc (5.2.x) linking failure when using CMake.
```
