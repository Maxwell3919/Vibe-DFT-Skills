# INPUT_CP — NAMELIST: &SYSTEM — Variable: tot_charge

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `000b6c46962a3ac24e7578f0996f50c2fd777ab43cfb3cb6127ec091654cac07`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       tot_charge
   
   Type:           REAL
   Default:        0.0
   Description:    total charge of the system. Useful for simulations with charged cells.
                   By default the unit cell is assumed to be neutral (tot_charge=0).
                   tot_charge=+1 means one electron missing from the system,
                   tot_charge=-1 means one additional electron, and so on.
                   
                   In a periodic calculation a compensating jellium background is
                   inserted to remove divergences if the cell is not neutral.
   +--------------------------------------------------------------------
   
```
