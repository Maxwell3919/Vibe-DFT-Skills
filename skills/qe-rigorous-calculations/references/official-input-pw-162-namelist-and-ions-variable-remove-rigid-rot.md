# INPUT_PW — NAMELIST: &IONS — Variable: remove_rigid_rot

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `1f94404615ee732738e6fb0dc181cce500614bf07a20ab10fdca8f2ea7e8539b`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
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
   
   ///---
      VARIABLES USED FOR MOLECULAR DYNAMICS
      
```
