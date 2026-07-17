# INPUT_CP — NAMELIST: &CELL — Variable: cell_temperature

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `4a9211bc7a0c30ba8c45eacc9f6e4cd75839318458275713d9e8e4104a4057e6`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       cell_temperature
   
   Type:           CHARACTER
   Default:        'not_controlled'
   Description:    'nose'            : control cell temperature using Nose thermostat
                                       see parameters "fnoseh" and "temph".
                   'rescaling'       : control cell temperature via velocities
                                       rescaling.
                   'not_controlled'  : cell temperature is not controlled.
   +--------------------------------------------------------------------
   
```
