# INPUT_PW — NAMELIST: &RISM — Variable: laue_wall

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `56e565feb3fc3d1a936b2399a812bcaed70351ae43838f390b4dae3460d14f7d`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       laue_wall
   
   Type:           CHARACTER
   Default:        'auto'
   Description:   
                   Set the repulsive wall with (1/r)^12 term of Lennard-Jones potential.
                   This is only for Laue-RISM.
    
                   'none' :
                        The repulsive wall is not defined.
    
                   'auto' :
                        The repulsive wall is defined, whose edge position is set automatically.
                        One does not have to set "laue_wall_z" (the edge position).
    
                   'manual' :
                        The repulsive wall is defined, whose edge position is set manually.
                        One have to set "laue_wall_z" (the edge position).
   +--------------------------------------------------------------------
   
```
