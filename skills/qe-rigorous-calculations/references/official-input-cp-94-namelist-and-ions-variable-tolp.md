# INPUT_CP — NAMELIST: &IONS — Variable: tolp

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `f4ef09ca6993c8ba432a5a1dd43ad6e22ff4cc849e88d195632a15e13849c7b8`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       tolp
   
   Type:           REAL
   Default:        100.D0
   Description:    tolerance (in Kelvin) of the rescaling. When ionic temperature
                   differs from "tempw" more than "tolp" apply rescaling.
                   meaningful only with "ion_temperature" = 'rescaling'
                   or with "ion_velocities"='change_step', where it specifies
                   the old timestep
   +--------------------------------------------------------------------
   
```
