# INPUT_PW — NAMELIST: &SYSTEM — Variable: exx_fraction

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `d0c5bde2e1ae24dfda3172e85596ed3e824de35e0c939fe2704241ad820f002e`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       exx_fraction
   
   Type:           REAL
   Default:        it depends on the specified functional
   Description:    Fraction of EXX for hybrid functional calculations. In the case of
                   "input_dft"='PBE0', the default value is 0.25, while for "input_dft"='B3LYP'
                   the "exx_fraction" default value is 0.20.
   +--------------------------------------------------------------------
   
```
