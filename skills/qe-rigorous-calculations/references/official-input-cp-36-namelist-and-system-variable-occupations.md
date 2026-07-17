# INPUT_CP — NAMELIST: &SYSTEM — Variable: occupations

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `cdda5af0de35193454021769cc2547d856451333ceecf76907c8cbf21d15050a`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       occupations
   
   Type:           CHARACTER
   Description:    a string describing the occupation of the electronic states.
                   Allowed values are 'fixed' (default) and 'ensemble'.
                   In the case of conjugate gradient style of minimization
                   of the electronic states, if occupations is set to 'ensemble',
                   this allows ensemble DFT calculations for metallic systems.
   +--------------------------------------------------------------------
   
```
