# INPUT_CP — NAMELIST: &IONS — Variable: ion_damping

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `52ca76d78fab20087b9c2734e644ad813519e59b677e1e3a8dd3838db29f30fb`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ion_damping
   
   Type:           REAL
   Default:        0.2D0
   Description:    damping frequency times delta t, optimal values could be
                     calculated with the formula :
                     SQRT( 0.5 * LOG( ( E1 - E2 ) / ( E2 - E3 ) ) )
                     where E1, E2, E3 are successive values of the DFT total energy
                     in a steepest descent simulations.
                     meaningful only if " ion_dynamics = 'damp' "
   +--------------------------------------------------------------------
   
```
