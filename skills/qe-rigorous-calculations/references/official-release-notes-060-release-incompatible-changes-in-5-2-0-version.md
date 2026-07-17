# Quantum ESPRESSO release notes — Incompatible changes in 5.2.0 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `c3594b2e8ba201d27f15853d6e0606068d129049e5e36f5f064efbe8a0450b58`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Incompatible changes in 5.2.0 version:

  * various "gather" and "scatter" routines removes and replaced by two
    interface routines gather_grid, scatter_grid, valid for all FFT grids
    and for both real and complex arrays; realspace_grid_init_custom and
    realspace_grids_init merged into realspace_grid_init, for each grid
  * __STD_F95 preprocessing option removed: all compilers that do not allow
    allocatable arrays in derived types are no longer supported
```
