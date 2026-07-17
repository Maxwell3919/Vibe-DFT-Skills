# INPUT_CP — NAMELIST: &WANNIER — Variable: exx_me_rcut_self

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `9e3b98f0681c88b9fc054d5dd35e23437ed13e80cead0e07fab193deba3ef2ac`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       exx_me_rcut_self
   
   Type:           REAL
   Default:        10.0
   Description:    Radial cutoff distance (in bohr) for the multipole-expansion sphere
                   centered at a given MLWF center.
                   The far-field self EXX potential in this sphere is generated with a
                   multipole expansion of the MLWF charge density.
                   This parameter must be larger than exx_ps_rcut_self by at least 3
                   real-space grid point spacings.
                   See J. Chem. Theory Comput. 16, 3757–3785 (2020).
   See:            exx_use_cube_domain
   +--------------------------------------------------------------------
   
```
