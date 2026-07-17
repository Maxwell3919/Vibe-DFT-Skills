# INPUT_CP — NAMELIST: &ELECTRONS — Variable: grease

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `45721350e1806b48ca0e56022b7fdb90b36cee14ab3a96dd0f8039766213ec03`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       grease
   
   Type:           REAL
   Default:        1.D0
   Description:    a number <= 1, very close to 1: the damping in electronic
                   damped dynamics is multiplied at each time step by "grease"
                   (avoids overdamping close to convergence: Obsolete ?)
                   grease = 1 : normal damped dynamics
   +--------------------------------------------------------------------
   
```
