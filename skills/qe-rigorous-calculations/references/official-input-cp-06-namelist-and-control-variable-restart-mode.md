# INPUT_CP — NAMELIST: &CONTROL — Variable: restart_mode

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `45ad70aeb332d9b19d3ea4809b4514df6b3c84f2fcbd0924d4d88922227b3074`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       restart_mode
   
   Type:           CHARACTER
   Default:        'restart'
   Description:    'from_scratch'   : from scratch
                   'restart'        : from previous interrupted run
                   'reset_counters' : continue a previous simulation,
                                      performs  "nstep" new steps, resetting
                                      the counter and averages
   +--------------------------------------------------------------------
   
```
