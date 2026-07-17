# INPUT_NEB — NAMELIST: &PATH — Variable: ds

- Official source: https://www.quantum-espresso.org/Doc/INPUT_NEB.txt
- Retrieved: 2026-07-17T11:49:26+00:00
- Official source SHA-256: `7c9f7e082b4846135e360fb86c0ce8a43f8e63825fa7d7fafcda3836a6088706`
- Extracted text SHA-256: `c7835abf054017fa52790be5b0f3d4e6abba1cc8373055639a7e3fd0dafabf02`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
         +--------------------------------------------------------------------
         Variable:       ds
         
         Type:           REAL
         Default:        1.D0
         Description:    Optimisation step length ( Hartree atomic units ).
                         If "opt_scheme"=="broyden", ds is used as a guess for the
                         diagonal part of the Jacobian matrix.
         +--------------------------------------------------------------------
         
         +--------------------------------------------------------------------
         Variables:      k_max, k_min
         
         Type:           REAL
         Default:        0.1D0 Hartree atomic units
         Description:    Set them to use a Variable Elastic Constants scheme
                         elastic constants are in the range [ k_min, k_max ]
                         this is useful to rise the resolution around the saddle point.
         +--------------------------------------------------------------------
         
```
