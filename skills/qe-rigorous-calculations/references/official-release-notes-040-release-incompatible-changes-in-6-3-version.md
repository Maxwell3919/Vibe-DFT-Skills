# Quantum ESPRESSO release notes — Incompatible changes in 6.3  version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `91522cca39ece53412bdf269de5c7251ce7632e3efe25f502ceeaf583ea6b4d2`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Incompatible changes in 6.3  version:

  * EPW: Removal of q-point paralelization (not very used and generated large code 
    duplication) ==> removal of the parallel_k and parallel_q input variables. 

  * various subroutines computing gradients and similar quantities using FFTs
    have been harmonized and collected into Modules/gradutils.f90

  * subroutine "ggen" split into two subroutines: "ggen" takes care of
    G-vectors for the FFT grid only, "ggens" for the subgrid only

  * FFT interfaces fwfft, invfft now accept only 'Rho', 'Wave', 'tgWave'.
    Together with FFT descriptor, these options cover all cases.

  * Structure for 'custom' FFT (exx_fft) deleted from exact exchange code,
    FFT descriptor dfftt and a few variables used instead
    (a different exx_fft structure is still present in GWW)

  * FFT indices nl, nlm, nls, nlsm, moved from their previous location
    (gvect, gvecs) into FFT descriptors (dfft* structures)

  * Development moved to GitLab
```
