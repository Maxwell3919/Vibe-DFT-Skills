# INPUT_ALL_CURRENTS — NAMELIST: &ENERGY_CURRENT — Variable: subtract_cm_vel

- Official source: https://www.quantum-espresso.org/Doc/INPUT_ALL_CURRENTS.txt
- Retrieved: 2026-07-17T11:48:53+00:00
- Official source SHA-256: `946599588fb07aee90e335384fccef11dacc6f7103defaed914bb052eb954434`
- Extracted text SHA-256: `c258cef39a90ee7c12815e9cf8ffe67794e1aa37989434f6b94a77a759eaabff`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       subtract_cm_vel
   
   Type:           LOGICAL
   Default:        .false.
   Description:    If true subtract from the velocities of all atoms for every step
                   the center of mass velocity for each atomic type.
                   It help to decorrelate a little the mass flux from the energy flux
   +--------------------------------------------------------------------
   
```
