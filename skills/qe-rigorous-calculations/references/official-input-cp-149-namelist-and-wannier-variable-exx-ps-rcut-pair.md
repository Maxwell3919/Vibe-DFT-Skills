# INPUT_CP — NAMELIST: &WANNIER — Variable: exx_ps_rcut_pair

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `33c3d0441d422f000c81075217d5c6010913d1e1de97011200d832b65e4cc218`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       exx_ps_rcut_pair
   
   Type:           REAL
   Default:        5.0
   Description:    Radial cutoff distance (in bohr) to compute the pair EXX energy.
                   This distance determines the radius of the Poisson sphere centered at
                   the midpoint of two overlapping MLWFs, and should be
                   large enough to cover the majority of the MLWF product density.
                   This parameter can generally be chosen as smaller than exx_ps_rcut_self.
                   See J. Chem. Theory Comput. 16, 3757–3785 (2020).
   See:            exx_use_cube_domain
   +--------------------------------------------------------------------
   
```
