# INPUT_PW — NAMELIST: &RISM — Variable: starting1d

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `587b55807bff476be8b805513a380798cf405cc4d79862322430e3b31fa805fb`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       starting1d
   
   Type:           CHARACTER
   Description:   
                   'zero' :
                        Starting correlation functions of 1D-RISM from zero.
                        ( default for scf, *relax, *md )
    
                   'file' :
                        Start from existing "1d-rism_csvv_r.xml" file in the
                        directory specified by variables "prefix" and "outdir".
    
                   'fix' :
                        Read from existing "1d-rism_csvv_r.xml" file in the
                        directory specified by variables "prefix" and "outdir",
                        and never calculate 1D-RISM.
                        For nscf and bands calculation this is the default.
   +--------------------------------------------------------------------
   
```
