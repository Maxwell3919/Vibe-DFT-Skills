# INPUT_ALL_CURRENTS — NAMELIST: &ENERGY_CURRENT — Variable: three_point_derivative

- Official source: https://www.quantum-espresso.org/Doc/INPUT_ALL_CURRENTS.txt
- Retrieved: 2026-07-17T11:48:53+00:00
- Official source SHA-256: `946599588fb07aee90e335384fccef11dacc6f7103defaed914bb052eb954434`
- Extracted text SHA-256: `acb959883f110149e983181547a199451ecf4c63424ee4612841a4a3444971f5`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       three_point_derivative
   
   Type:           LOGICAL
   Default:        .true.
   Description:    If true calculates three ground stated: one at t - "delta_t" /2, one at t and one at t + "delta_t"/2.
                   Obviously it needs more computer time, but the derivative should be better.
   +--------------------------------------------------------------------
   
```
