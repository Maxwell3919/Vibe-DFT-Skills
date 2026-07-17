# INPUT_CP — NAMELIST: &PRESS_AI — Variable: pvar

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `fec66ada0a519a89cff52496397d58607096cd9fc717bfdf50a165e0a097b45c`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       pvar
   
   Type:           LOGICAL
   Default:        .false.
   Description:    .true. for variable pressure calculations
                   pressure changes linearly with time:
                   Delta_P = (P_fin - P_in)/nstep
   +--------------------------------------------------------------------
   
```
