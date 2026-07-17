# INPUT_PW — NAMELIST: &SYSTEM — Variable: input_dft

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `bba4177c75046b8bf3bc657fb10206aa780e5c5ba042365c5bcace43205826c7`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       input_dft
   
   Type:           CHARACTER
   Default:        read from pseudopotential files
   Description:    Exchange-correlation functional: eg 'PBE', 'BLYP' etc
                   See Modules/funct.f90 for allowed values.
                   Overrides the value read from pseudopotential files.
                   Use with care and if you know what you are doing!
   +--------------------------------------------------------------------
   
```
