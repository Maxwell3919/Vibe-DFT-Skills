# INPUT_CP — NAMELIST: &IONS — Variable: fnosep

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `f2e0ad6dbe93b4a59027c41921c65015dd2e171734c32304fcced4f7a3a14ea0`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       fnosep
   
   Type:           REAL
   Default:        1.D0
   Description:    oscillation frequency of the nose thermostat (in terahertz)
                   [note that 3 terahertz = 100 cm^-1]
                   meaningful only with " ion_temperature = 'nose' "
                   for Nose-Hoover chain one can set frequencies of all thermostats
                   ( fnosep = X Y Z etc. ) If only first is set, the defaults for
                   the others will be same.
   +--------------------------------------------------------------------
   
```
