# Quantum ESPRESSO release notes — Fixed in version 4.2.1:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `f7672d239601f3b84ce9b47c9d77c664b0f5e781140fbf9eb67582da767da8cd`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 4.2.1:

  * CP: problem in electronic forces with OpenMP parallelization
  * real-space Q functions (tqr=.true.) not working in non-collinear case
  * XC potential in CP was not initialized when condition (rho > 10^(-30)) 
    was not satisfied; this is usually harmless but potentially dangerous
  * CP could not read data written from PW in spin-polarized cases
  * In at least some cases, cpmd2upf.x was yielding incorrect PPs
  * support for MKL incomplete (only in packaged version, not in cvs)
  * glitch in pw2wannier if / missing at the end of outdir
  * linking error when compiling qexml
  * misc problems in plotband.f90
  * the new G-space symmetrization was not working properly 
    for the magnetization in the non-collinear case
  * CP: incorrect results in parallel execution if the card K_POINTS
    was present in input and contained a point different from Gamma
  * D3: Fermi energy shift was only symmetrized on the sub-set of the
    symmetry operations that leave q unchanged.
  * plot_io.f90: for large celldm(1), there was no space between ibrav 
    and celldm. Courtesy of E. Li.
  * A problem in projwfc in the spin-orbit case introduced in version 4.1.3.
    Courtesy of R. Mazzarello.  

                               * * * * *
```
