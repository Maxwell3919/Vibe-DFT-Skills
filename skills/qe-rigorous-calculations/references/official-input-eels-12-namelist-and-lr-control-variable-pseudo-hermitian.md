# INPUT_EELS — NAMELIST: &LR_CONTROL — Variable: pseudo_hermitian

- Official source: https://www.quantum-espresso.org/Doc/INPUT_EELS.txt
- Retrieved: 2026-07-17T11:49:13+00:00
- Official source SHA-256: `c884578523001dc82364d82882329e7743ca966c353a3e21c94684a4be8f9e54`
- Extracted text SHA-256: `5ec7771cbbecd7f836c63c5143d7919978526f47d2d84540289b4135639b8d8f`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:24 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       pseudo_hermitian
   
   Type:           LOGICAL
   Default:        .true.
   Description:    This variable is used only when "calculator" = 'lanczos'.
                   When set to .true. the pseudo-Hermitian Lanczos algorithm is
                   used. When set to .false. the non-Hermitian Lanczos
                   biorthogonalization algorithm is used (which is two times slower).
   +--------------------------------------------------------------------
   
```
