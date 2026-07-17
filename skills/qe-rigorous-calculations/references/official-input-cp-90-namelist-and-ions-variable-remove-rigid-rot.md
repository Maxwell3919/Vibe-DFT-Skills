# INPUT_CP — NAMELIST: &IONS — Variable: remove_rigid_rot

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `292a6905991ad7328ea00a03e28a6e87d2507839bbea4ac893bd83c432bf3dc1`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       remove_rigid_rot
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    This keyword is useful when simulating the dynamics and/or the
                   thermodynamics of an isolated system. If set to true the total
                   torque of the internal forces is set to zero by adding new forces
                   that compensate the spurious interaction with the periodic
                   images. This allows for the use of smaller supercells.
                   
                   BEWARE: since the potential energy is no longer consistent with
                   the forces (it still contains the spurious interaction with the
                   repeated images), the total energy is not conserved anymore.
                   However the dynamical and thermodynamical properties should be
                   in closer agreement with those of an isolated system.
                   Also the final energy of a structural relaxation will be higher,
                   but the relaxation itself should be faster.
   +--------------------------------------------------------------------
   
```
