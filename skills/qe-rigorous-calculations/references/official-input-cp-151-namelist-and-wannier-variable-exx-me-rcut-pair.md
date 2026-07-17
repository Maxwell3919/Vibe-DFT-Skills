# INPUT_CP — NAMELIST: &WANNIER — Variable: exx_me_rcut_pair

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `2db2fda801857bb3d4d7f02a97109b805243ce3079d18649d0c76825543d642f`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       exx_me_rcut_pair
   
   Type:           REAL
   Default:        7.0
   Description:    Radial cutoff distance (in bohr) for the multipole-expansion sphere
                   centered at the midpoint of two overlapping MLWFs.
                   The far-field pair EXX potential in this sphere is generated with
                   a multipole expansion of the MLWF product density.
                   This parameter must be larger than exx_ps_rcut_pair by at least 3
                   real-space grid point spacings. Also, this parameter can generally
                   be chosen as smaller than exx_me_rcut_self.
                   See J. Chem. Theory Comput. 16, 3757–3785 (2020).
   See:            exx_use_cube_domain
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


========================================================================
```
