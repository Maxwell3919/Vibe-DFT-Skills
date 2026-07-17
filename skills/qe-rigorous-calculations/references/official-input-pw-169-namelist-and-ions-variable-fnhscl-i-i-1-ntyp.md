# INPUT_PW — NAMELIST: &IONS — Variable: fnhscl(i), i=1,ntyp

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `792acc23b74096ed08571f73fec3d01ede17b9b9dab8453674b697aed98c42d7`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
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
