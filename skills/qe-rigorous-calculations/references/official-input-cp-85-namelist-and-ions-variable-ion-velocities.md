# INPUT_CP — NAMELIST: &IONS — Variable: ion_velocities

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `9c19874c1cebc8e030d90cca27058c1975c3b0117ad61ed758c5c47aa6b76bdd`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ion_velocities
   
   Type:           CHARACTER
   Default:        'default'
   See:            tempw
   Description:    initial ionic velocities
                   'default'     : restart the simulation with atomic velocities read
                                   from the restart file
                   'change_step' : restart the simulation with atomic velocities read
                                   from the restart file, with rescaling due to the
                                   timestep change, specify the old step via "tolp"
                                   as in tolp = 'old_time_step_value' in au.
                                   Note that you may want to specify
                                   electron_velocities = 'change_step'
                   'random'      : start the simulation with random atomic velocities
                                   (see also variable "tempw")
                   'from_input'  : restart the simulation with atomic velocities read
                                   from standard input - see card 'ATOMIC_VELOCITIES'
                                   BEWARE: tested only with electrons_dynamics='cg'
                   'zero'        : restart the simulation with atomic velocities set
                                   to zero
   +--------------------------------------------------------------------
   
```
