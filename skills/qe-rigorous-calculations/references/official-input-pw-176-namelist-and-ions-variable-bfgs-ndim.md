# INPUT_PW — NAMELIST: &IONS — Variable: bfgs_ndim

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `47672f8bd4dbeec33c9d61ec2824d580bd30db931d8037d79b20eb90e1de10cd`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       bfgs_ndim
      
      Type:           INTEGER
      Default:        1
      Description:    Number of old forces and displacements vectors used in the
                      PULAY (GDIIS) mixing of the residual vectors obtained on the basis
                      of the inverse hessian matrix given by the BFGS algorithm.
                      The variable  "tgdiis_step" in this case sets whether to use to full GDIIS step
                      or the BFGS trust_radius.
                      When "bfgs_ndim" = 1, the standard quasi-Newton BFGS method is
                      used.
                      (bfgs only)
      +--------------------------------------------------------------------
      
```
