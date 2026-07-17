# INPUT_PW — NAMELIST: &IONS — Variable: ion_velocities

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `5b45c926cc6ede27601cb76fac89f3f303c18477c95f2d2214c32946c67f62ed`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ion_velocities
   
   Type:           CHARACTER
   Default:        'default'
   Description:   
                   Initial ionic velocities. Available options are:
    
                   'default' :
                        start a new simulation from random thermalized
                        distribution of velocities if "tempw" is set,
                        with zero velocities otherwise; restart from
                        atomic velocities read from the restart file
    
                   'from_input' :
                        start or continue the simulation with atomic
                        velocities read from standard input - see card
                        "ATOMIC_VELOCITIES"
   +--------------------------------------------------------------------
   
```
