# INPUT_PW — NAMELIST: &CONTROL — Variable: twochem

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `2892db39cbd03aec90724d7ac0bbc3c7ffaf3c7e171e786398265997bdd801fe`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       twochem
   
   Type:           LOGICAL
   Default:        .FALSE.
   See:            nelec_cond, nbnd_cond, degauss_cond
   Description:    IF .TRUE. , a two chemical potential calculation for the simulation of
                   photoexcited systems is performed, constraining a fraction of the
                   electrons in the conduction manifold.
                   See G. Marini, M. Calandra; PRB 104, 144103 (2021).
                   Note: requires "occupations" to be set to 'smearing'.
   +--------------------------------------------------------------------
   
```
