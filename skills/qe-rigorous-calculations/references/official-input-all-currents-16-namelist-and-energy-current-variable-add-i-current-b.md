# INPUT_ALL_CURRENTS — NAMELIST: &ENERGY_CURRENT — Variable: add_i_current_b

- Official source: https://www.quantum-espresso.org/Doc/INPUT_ALL_CURRENTS.txt
- Retrieved: 2026-07-17T11:48:53+00:00
- Official source SHA-256: `946599588fb07aee90e335384fccef11dacc6f7103defaed914bb052eb954434`
- Extracted text SHA-256: `b34d74b924f491b2c3ab1eb91ee0e94e0bc4a9ca229257f411d62ca94e18fcbf`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       add_i_current_b
   
   Type:           LOGICAL
   Default:        .false.
   Description:    If true adds to the energy current a part that is correctly implemented only for cubic cells.
                   This part is in the form of a sum over the atomic types of a constant time the center of mass velocity
                   of the atomic type. It does not change the value of the thermal conductivity when the formula for the
                   multicomponent case with the inverse of the Schur complement is used, and in the single component
                   or solid case this is a non-diffusive contribution.
   +--------------------------------------------------------------------
   
```
