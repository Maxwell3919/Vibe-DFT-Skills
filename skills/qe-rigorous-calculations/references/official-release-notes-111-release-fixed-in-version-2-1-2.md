# Quantum ESPRESSO release notes — Fixed in version 2.1.2:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `6257a1e567157c9df847efebcf1b47fb285e2728e7265f2295313779fad4d272`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 2.1.2:

  * The phonon code was yielding incorrect results when 4-dimensional 
    irreps were present (i.e. A point in graphite) and ultrasoft PP used
    (reported by Nicolas Mounet)
  * in some cases ld1 was writing a bad UPF file
  * in some cases the charge density was not conserved during
    the charge mixing
  * various problems with potential extrapolation in neb and smd
  * variable-cell dynamics and optimization was not working in parallel
  * Berry phase calculation in parallel should have been disabled
  * bug in readfile_config when restarting without a "*.save" file
  * crash in pw2casino due to bad call to v_of_rho

                                 * * * * *
```
