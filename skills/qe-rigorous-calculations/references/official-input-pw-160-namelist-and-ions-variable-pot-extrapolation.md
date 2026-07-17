# INPUT_PW — NAMELIST: &IONS — Variable: pot_extrapolation

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `78f5f547e2d60b3612f33fe4e2b6cc40d4c4874fc9a538cd9d4dabaea47c24a8`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       pot_extrapolation
   
   Type:           CHARACTER
   Default:        'atomic'
   Description:   
                   Used to extrapolate the potential from preceding ionic steps.
    
                   'none' :
                        no extrapolation
    
                   'atomic' :
                        extrapolate the potential as if it was a sum of
                        atomic-like orbitals
    
                   'first_order' :
                        extrapolate the potential with first-order
                        formula
    
                   'second_order' :
                        as above, with second order formula
    
                   Note: 'first_order' and 'second-order' extrapolation make sense
                   only for molecular dynamics calculations
   +--------------------------------------------------------------------
   
```
