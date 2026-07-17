# INPUT_PW — NAMELIST: &SYSTEM — Variable: tot_charge

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `1d3cf99ed25c9c0f8cd061311ec999eb8b8085a8a40bd384a061e0c9ad60c100`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       tot_charge
   
   Type:           REAL
   Default:        0.0
   Description:    Total charge of the system. Useful for simulations with charged cells.
                   By default the unit cell is assumed to be neutral (tot_charge=0).
                   tot_charge=+1 means one electron missing from the system,
                   tot_charge=-1 means one additional electron, and so on.
                   
                   In a periodic calculation a compensating jellium background is
                   inserted to remove divergences if the cell is not neutral.
   +--------------------------------------------------------------------
   
```
