# INPUT_CP — NAMELIST: &SYSTEM — Variable: Hubbard_U(i), i=1,ntyp

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `15b3b00434be7cfa91a4b0fbb2d0c183dc531403c2669f62fab559cdce1ca402`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       Hubbard_U(i), i=1,ntyp
   
   Type:           REAL
   Default:        0.D0 for all species
   Status:         LDA+U works only for a few selected elements. Modify
                   CPV/ldaU.f90 if you plan to use LDA+U with an
                   element that is not configured there.
   Description:    Hubbard_U(i): parameter U (in eV) for LDA+U calculations.
                   Currently only the simpler, one-parameter LDA+U is
                   implemented (no "alpha" or "J" terms)
   +--------------------------------------------------------------------
   
```
