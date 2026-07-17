# INPUT_CP — NAMELIST: &ELECTRONS — Variable: electron_velocities

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `edfbd9feca32bb582e868ea9a8807c2375c3876ede1828aa646c343b4559f65f`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       electron_velocities
   
   Type:           CHARACTER
   Description:    'zero'      : restart setting electronic velocities to zero
                   'default'   : restart using electronic velocities of the
                               previous run
                   'change_step' : restart simulation using electronic velocities of the
                               previous run, with rescaling due to the timestep change.
                               specify the old step via "tolp" as in
                               tolp = 'old_time_step_value' in au.
                               Note that you may want to specify
                               "ion_velocities" = 'change_step'
   +--------------------------------------------------------------------
   
```
