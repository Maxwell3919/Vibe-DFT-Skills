# INPUT_PW — NAMELIST: &ELECTRONS — Variable: efield_phase

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `d69165b4ca4a9333e9181a618439fb7109142195c87341359963b793dd740b6b`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       efield_phase
   
   Type:           CHARACTER
   Default:        'none'
   Description:   
                   Available options are:
    
                   'read' :
                        set the zero of the electronic polarization (with "lelfield"==.true..)
                        to the result of a previous calculation
    
                   'write' :
                        write on disk data on electronic polarization to be read in another
                        calculation
    
                   'none' :
                        none of the above points
   +--------------------------------------------------------------------
   
```
