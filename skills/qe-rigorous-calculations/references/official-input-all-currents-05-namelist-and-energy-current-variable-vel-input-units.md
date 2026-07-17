# INPUT_ALL_CURRENTS — NAMELIST: &ENERGY_CURRENT — Variable: vel_input_units

- Official source: https://www.quantum-espresso.org/Doc/INPUT_ALL_CURRENTS.txt
- Retrieved: 2026-07-17T11:48:53+00:00
- Official source SHA-256: `946599588fb07aee90e335384fccef11dacc6f7103defaed914bb052eb954434`
- Extracted text SHA-256: `e6c935179afb1447cc39cb84f2d09166d555a9f35f1194f72d3fb9175cc7d646`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       vel_input_units
   
   Type:           CHARACTER
   Default:        'PW'
   Description:   
                   This multiplies or not by a factor 2 the velocities given in the input.
                                         Available options are:
    
                   'CP' :
                        assume velocities are given in cp.x time units (thus multiplying by 2 the velocities)
    
                   'PW' :
                        assume velocities are given in pw.x time units
   +--------------------------------------------------------------------
   
```
