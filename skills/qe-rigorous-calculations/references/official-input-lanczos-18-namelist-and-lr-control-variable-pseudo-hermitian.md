# INPUT_Lanczos — NAMELIST: &LR_CONTROL — Variable: pseudo_hermitian

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Lanczos.txt
- Retrieved: 2026-07-17T11:49:18+00:00
- Official source SHA-256: `58c02f4cb1fdefbef4203bbe55d16af2a768acd7cfb5462fc62bd1dfd07cb530`
- Extracted text SHA-256: `c48fb454ea0e946b2ea70f0c1279e8a34ecea6ebde1002297c9389c8c8f98676`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       pseudo_hermitian
   
   Type:           LOGICAL
   Default:        .true.
   Description:    When set to .true. the pseudo-Hermitian Lanczos
                   algorithm is used. When set to .false. the
                   non-Hermitian Lanczos biorthogonalization algorithm
                   is used (which is two times slower).
   +--------------------------------------------------------------------
   
```
