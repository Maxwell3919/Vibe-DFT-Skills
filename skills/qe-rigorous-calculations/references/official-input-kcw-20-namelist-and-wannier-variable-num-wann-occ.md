# INPUT_kcw — NAMELIST: &WANNIER — Variable: num_wann_occ

- Official source: https://www.quantum-espresso.org/Doc/INPUT_kcw.txt
- Retrieved: 2026-07-17T11:49:55+00:00
- Official source SHA-256: `0e051e12dbf1f904e8044c5f2fc1f44a8e2f8f72f29e687d4fd675364d26e3d0`
- Extracted text SHA-256: `3112a04d2a6fba8cdc8ae03e870ebeb7165b7d34d4ccc99a861d02c2d15e0157`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       num_wann_occ
   
   Type:           INTEGER
   Default:        0
   Description:    The number of wannier function for the occupied manifold.
                   It has to coincide with the number of occupied KS orbitals.
                   The whole KS manifold has to be wannierised (no 'exclude_band'
                   option for occupied state, at the moment).
   +--------------------------------------------------------------------
   
```
