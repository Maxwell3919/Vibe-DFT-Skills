# Quantum ESPRESSO release notes — Fixed in 6.7 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `bf2ff1ae60fc0ebfd7b5bcef6a7f6f85ad1e4376f7967e78048a95d8e16f38e2`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 6.7 version:
  * Some linkers yield "missing references to ddot_" in libbeef
  * Bogus errors in scale_sym_ops in some cases of almost-symmetric crystals
  * FFT test in FFTXlib was not always compiling 
  * angle1, angle2, starting_magnetization incorrectly written to xml file
  * Bug in Hubbard forces and stress for bands parallelization (when nproc_pool>nbnd) 
  * Bug in DFT+U+V when starting_ns_eigenvalue is used (courtesy of M. Cococcioni)
  * Crash in the calculation of Z* with ultrasoft PP when the number of bands
    is larger than the number of occupied bands (thanks to Sasha Fonari)
  * Crash in matdyn.x when ibrav=0 (thanks to Sasha Fonari)
  * Some postprocessing cases not working properly with k-point parallelization
    and ultrasoft pseudopotentials (noticed by Kristjan Eimre)
  * Ensemble dynamics in CP was broken in v.6.6 (not in previous versions)
```
