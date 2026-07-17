# INPUT_CP — NAMELIST: &IONS — Variable: tempw

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `31b3f375474696e2ad9bb4ff0208f705246a0936cec4fe358a7ee6ff0e39d040`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       tempw
   
   Type:           REAL
   Default:        300.D0
   Description:    value of the ionic temperature (in Kelvin) forced by the
                   temperature control.
                   meaningful only with " ion_temperature /= 'not_controlled' "
                   or when the initial velocities are set to 'random'
                   "ndega" controls number of degrees of freedom used in
                   temperature calculation
   +--------------------------------------------------------------------
   
```
