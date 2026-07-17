# INPUT_BAND_INTERPOLATION — NAMELIST: &INTERPOLATION — Variable: scale_sphere

- Official source: https://www.quantum-espresso.org/Doc/INPUT_BAND_INTERPOLATION.txt
- Retrieved: 2026-07-17T11:48:56+00:00
- Official source SHA-256: `b60e3891af78fc24ae40985e172e19ff674772d57eebe438f62dfd9a1e7a331f`
- Extracted text SHA-256: `929f7a6fb6a383f4c6252bdd5ea58ab5eca1f4e376f90950bdd8771f12cd991f`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       scale_sphere
   
   Type:           INTEGER
   Default:        4.0d0
   Description:    The search radius for "method" == 'idw-sphere', is Rmin * scale_sphere, where Rmin is the
                                     minimum distance found between the uniform grid of k-points.
                   
                                     If scale_sphere is too small, some k-points of the path might not see enough uniform grid points
                                     to average energies, whereas for large values the method becomes equal to "method" == 'idw'.
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


========================================================================
```
