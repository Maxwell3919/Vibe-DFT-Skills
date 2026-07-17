# Quantum ESPRESSO release notes — New in 5.1 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `86d3cfc2d51961df253fc78e82e4955557467167718a14603c91f4cbf4f5d7f3`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
New in 5.1 version:

  * "Cold restart" for Car-Parrinello dynamics
  * Calling QE from external codes made easier: see new subdirectory COUPLE
  * PW: Hybrid functionals for USPP and PAW (experimental)
  * PW: partial support to the use of k-point labels in the Brillouin zone
  * PW: Langevin dynamics with Smart Monte Carlo
  * CP and PW: Tkatchenko-Scheffler vdW correction (experimental)
  * GWW replaced by GWL (using Lanczos chains)
  * turboTDDFT: pseudo_Hermitian Lanczos algorithm and 
    Davidson-like diagonalization added
  * PWCOND with DFT+U
  * New functionals: gau-pbe, PW86 (unrevised), B86B, XDM (exchange-hole 
    dipole moment) model of dispersions, vdW-DF-obk8, vdW-DF-ob86 (Klimes
    et al), rVV10, vdW-DF2-b86r
  * PHonon: Calculation of phonon dispersions using the finite displacements 
    supercell approach. See subdirectory FD/ in PHonon.
  * dynmat.x can calculate phonon contribution to dielectric tensor
  * turboTDDFT now supports hybrid functionals (only with norm-conserving
    pseudopotentials)
  * "image" parallelization re-introduced in pw.x: see code "manypw.x"
```
