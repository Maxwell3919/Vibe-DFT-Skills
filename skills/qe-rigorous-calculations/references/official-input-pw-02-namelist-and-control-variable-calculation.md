# INPUT_PW — NAMELIST: &CONTROL — Variable: calculation

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `098076ab76f4afb1eb4c0c8d291e3ed424be2bc71eb7f92de6009f30baf0f89d`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       calculation
   
   Type:           CHARACTER
   Default:        'scf'
   Description:   
                   A string describing the task to be performed. Options are:
                        'scf'
                        'nscf'
                        'bands'
                        'relax'
                        'md'
                        'vc-relax'
                        'vc-md'
    
                   (vc = variable-cell).
   +--------------------------------------------------------------------
   
```
