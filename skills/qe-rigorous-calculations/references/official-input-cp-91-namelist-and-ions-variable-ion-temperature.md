# INPUT_CP — NAMELIST: &IONS — Variable: ion_temperature

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `7220eb644cfe597b9bc63d3d87df0d0eb52795e2755979d15eafc86c36d5d565`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ion_temperature
   
   Type:           CHARACTER
   Default:        'not_controlled'
   Description:    'nose'           : control ionic temperature using Nose-Hoover
                                      thermostat  see parameters "fnosep", "tempw",
                                      "nhpcl", "ndega", "nhptyp"
                   'rescaling'      : control ionic temperature via velocities
                                      rescaling. see parameter "tolp"
                   'not_controlled' : ionic temperature is not controlled
   +--------------------------------------------------------------------
   
```
