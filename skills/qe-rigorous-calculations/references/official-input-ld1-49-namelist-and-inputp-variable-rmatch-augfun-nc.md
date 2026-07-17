# INPUT_LD1 — NAMELIST: &INPUTP — Variable: rmatch_augfun_nc

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `531b42cc659efb6829f5038ce09deb99d1eac7f13255bf2b7a6f89777da53992`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       rmatch_augfun_nc
      
      Type:           REAL
      Default:        .false.
      Status:         Used only if which_augfun is 'PSQ'.
      Description:    If .true. the augmentation functions are pseudized
                      from the origin to min(rcut(ns),rcut(ns1)) where ns
                      and ns1 are the two channels for that Q. In this case
                      rmatch_augfun is not used.
      +--------------------------------------------------------------------
      
   \\\---
   
```
