# INPUT_CP — NAMELIST: &WANNIER — Variable: exx_use_cube_domain

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `358bf6983a5a28d968e5382ffa33c612b41fae38250aa48f213593fe9ea2e2b0`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       exx_use_cube_domain
   
   Type:           LOGICAL
   Default:        .false.
   Description:    Use cubic instead of spherical subdomains as local supports during computation
                   of the EXX potential. If set to .TRUE., the spherical domain
                   radii (exx_ps_rcut_self, exx_ps_rcut_pair, exx_me_rcut_self, exx_me_rcut_pair)
                   will be treated as half of the side length of the cubic subdomain.
   +--------------------------------------------------------------------
   
```
