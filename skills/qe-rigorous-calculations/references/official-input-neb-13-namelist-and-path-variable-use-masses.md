# INPUT_NEB — NAMELIST: &PATH — Variable: use_masses

- Official source: https://www.quantum-espresso.org/Doc/INPUT_NEB.txt
- Retrieved: 2026-07-17T11:49:26+00:00
- Official source SHA-256: `7c9f7e082b4846135e360fb86c0ce8a43f8e63825fa7d7fafcda3836a6088706`
- Extracted text SHA-256: `b06bda35982959cd62a714d9502d1c6ac431f8d1bbea4da9b0ebe47d283f449b`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
         +--------------------------------------------------------------------
         Variable:       use_masses
         
         Type:           LOGICAL
         Default:        .FALSE.
         Description:    If. TRUE. the optimisation of the path is performed using
                         mass-weighted coordinates. Useful together with quick-min
                         optimization scheme, if some bonds are much stiffer than
                         others. By assigning a larger (fictitious) mass to atoms
                         with stiff bonds, one may use a longer time step "ds"
         +--------------------------------------------------------------------
         
```
