# INPUT_LD1 — NAMELIST: &INPUTP — Variable: which_augfun

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `6be05ec8dd93e464a466ecf671aab06802fb201ca354eb52038003fb86d62835`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       which_augfun
      
      Type:           CHARACTER
      Default:        'AE' for Vanderbilt-Ultrasoft pseudo-potentials and 'BESSEL' for PAW datasets.
      Description:    If different from 'AE' the augmentation functions are pseudized
                      before "rmatch_augfun". The pseudization options are:
                      
                      * 'PSQ'        Use Bessel functions to pseudize Q
                                     from the origin to rmatch_augfun.
                      
                      These features are available only for PAW:
                      
                      * 'BESSEL'     Use Bessel functions to pseudize the Q.
                      * 'GAUSS'      Use 2 Gaussian functions to pseudize the Q.
                      * 'BG'         Use original Bloechl's recipe with a single gaussian.
                      
                      Note: if lpaw is true and which_augfun is set to AE real all-
                      electron charge will be used, which will produce extremely
                      hard augmentation.
      +--------------------------------------------------------------------
      
```
