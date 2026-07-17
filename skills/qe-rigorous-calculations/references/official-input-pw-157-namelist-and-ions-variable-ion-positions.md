# INPUT_PW — NAMELIST: &IONS — Variable: ion_positions

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `d4c124050c562683e350baee625ab930c6629eae6ba32aeff73dd3608e8a7ee9`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ion_positions
   
   Type:           CHARACTER
   Default:        'default'
   Description:   
                   Available options are:
    
                   'default' :
                        if restarting, use atomic positions read from the
                        restart file; in all other cases, use atomic
                        positions from standard input.
    
                   'from_input' :
                        read atomic positions from standard input, even if restarting.
   +--------------------------------------------------------------------
   
```
