# INPUT_Davidson — NAMELIST: &LR_DAV — Variable: reference

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Davidson.txt
- Retrieved: 2026-07-17T11:49:12+00:00
- Official source SHA-256: `3119323bee658797174ac83c6f304a99ae95949a07ca87563de949ec1243341c`
- Extracted text SHA-256: `e121da9395e03270b80d8f7a9f503ec0b2038447044be2d535219db41f552c8f`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       reference
   
   Type:           REAL
   Default:        0.0d0
   Description:    Reference energy in units of Ry. This variable is used
                   to constrain the Davidson algorithm to converge the eigenstates
                   having the energy closest to the reference energy. In this way
                   one can calculate less eigenstates at once, and to perform multiple
                   calculations with different reference energies (the post-processing
                   code tddfpt_calculate_spectrum.x can be used for this purpose).
   +--------------------------------------------------------------------
   
```
