# INPUT_CP — NAMELIST: &ELECTRONS — Variable: electron_temperature

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `e4b84a00b63aebb77d3326c5f7c517577592b0bdcb13675d6e17897da9e90edc`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       electron_temperature
   
   Type:           CHARACTER
   Default:        'not_controlled'
   Description:    'nose'            : control electronic temperature using Nose
                                     thermostat. See also "fnosee" and "ekincw".
                   'rescaling'       : control electronic temperature via velocities
                                     rescaling.
                   'not_controlled'  : electronic temperature is not controlled.
   +--------------------------------------------------------------------
   
```
