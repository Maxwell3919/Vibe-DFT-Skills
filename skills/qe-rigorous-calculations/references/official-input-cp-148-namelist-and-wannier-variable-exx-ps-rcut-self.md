# INPUT_CP — NAMELIST: &WANNIER — Variable: exx_ps_rcut_self

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `1af6c7c266f1ea3c843211354345df2a98f0a080dabd6df3140e3b4c0703eca7`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       exx_ps_rcut_self
   
   Type:           REAL
   Default:        6.0
   Description:    Radial cutoff distance (in bohr) to compute the self EXX energy.
                   This distance determines the radius of the Poisson sphere centered at
                   a given MLWF center, and should be large enough to cover
                   the majority of the MLWF charge density.
                   See J. Chem. Theory Comput. 16, 3757–3785 (2020).
   See:            exx_use_cube_domain
   +--------------------------------------------------------------------
   
```
