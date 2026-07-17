# INPUT_PW — NAMELIST: &SYSTEM — Variable: xdm_a2

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `f02341c0ddde1aa2673dab79ca6efb3102b3baab0f24b6745f22da2f73c88778`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       xdm_a2
   
   Type:           REAL
   Default:        1.5045
   Description:    Damping function parameter a2 (angstrom). It is NOT necessary to give
                   a value if the functional is one of B86bPBE, PW86PBE, PBE, BLYP. For functionals
                   in this list, the coefficients are given in:
                      https://github.com/aoterodelaroza/postg/blob/master/xdm.param
                      or https://erin-r-johnson.github.io/software/
                      A. Otero de la Roza, E. R. Johnson, J. Chem. Phys. 138, 204109 (2013),
                      doi:10.1063/1.4705760
   +--------------------------------------------------------------------
   
```
