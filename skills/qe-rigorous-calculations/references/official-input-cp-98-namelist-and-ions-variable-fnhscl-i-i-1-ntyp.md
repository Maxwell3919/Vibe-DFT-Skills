# INPUT_CP — NAMELIST: &IONS — Variable: fnhscl(i), i=1,ntyp

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `04ad3d840b3a6e041bdd1ba6452e94c0389469deba94f5f7e60ed404c58464dc`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       fnhscl(i), i=1,ntyp
   
   Type:           REAL
   Default:        (Nat_{total}-1)/Nat_{total}
   Description:    these are the scaling factors to be used together with nhptyp=3 and nhgrp(i)
                   in order to take care of possible reduction in the degrees of freedom due to
                   constraints. Suppose that with the previous example HCOOLi, C-H bond is
                   constrained. Then, these 2 atoms will have 5 degrees of freedom in total instead
                   of 6, and one can set fnhscl={5/6 5/6 1. 1.}. This way the target kinetic energy
                   for H&C will become 6(kT/2)*5/6 = 5(kT/2). This option is to be used for
                   simulations with many constraints, such as rigid water with something else in there
   +--------------------------------------------------------------------
   
```
