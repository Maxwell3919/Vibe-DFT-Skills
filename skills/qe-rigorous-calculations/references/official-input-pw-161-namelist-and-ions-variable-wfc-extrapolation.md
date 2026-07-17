# INPUT_PW — NAMELIST: &IONS — Variable: wfc_extrapolation

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `583ec5e7546ca92ee2ceb0bc61ccacdc2fcb796fc456de6a5c3604f35e07fb82`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       wfc_extrapolation
   
   Type:           CHARACTER
   Default:        'none'
   Description:   
                   Used to extrapolate the wavefunctions from preceding ionic steps.
    
                   'none' :
                        no extrapolation
    
                   'first_order' :
                        extrapolate the wave-functions with first-order formula.
    
                   'second_order' :
                        as above, with second order formula.
    
                   Note: 'first_order' and 'second-order' extrapolation make sense
                   only for molecular dynamics calculations
   +--------------------------------------------------------------------
   
```
