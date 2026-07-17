# INPUT_CP — NAMELIST: &CONTROL — Variable: prefix

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `232d3e1aa2b944cddf36d519c379e47904b4b32dced239fc48c30ff55842c1be`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       prefix
   
   Type:           CHARACTER
   Default:        'cp'
   Description:    prepended to input/output filenames and restart folders:
                     prefix.pos : atomic positions
                     prefix.vel : atomic velocities
                     prefix.for : atomic forces
                     prefix.cel : cell parameters
                     prefix.str : stress tensors
                     prefix.evp : energies
                     prefix.hrs : Hirshfeld effective volumes (ts-vdw)
                     prefix.eig : eigen values
                     prefix.nos : Nose-Hoover variables
                     prefix.spr : spread of Wannier orbitals
                     prefix.wfc : center of Wannier orbitals
                     prefix.ncg : number of Poisson CG steps (PBE0)
                     prefix_ndw.save/ : write restart folder
                     prefix_ndr.save/ : read restart folder
                   where ndr and ndw are the integers number described below
   +--------------------------------------------------------------------
   
```
