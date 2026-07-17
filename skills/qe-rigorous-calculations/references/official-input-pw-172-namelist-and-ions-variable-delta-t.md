# INPUT_PW — NAMELIST: &IONS — Variable: delta_t

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `8a4bea12f4ea0677a75df9d966079da035126edb96ca3c4158fce1ab20d517dd`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       delta_t
      
      Type:           REAL
      Default:        1.D0
      Description:    if "ion_temperature" == 'rescale-T' :
                             at each step the instantaneous temperature is multiplied
                             by delta_t; this is done rescaling all the velocities.
                      
                      if "ion_temperature" == 'reduce-T' :
                             every 'nraise' steps the instantaneous temperature is
                             reduced by -"delta_t" (i.e. "delta_t" < 0 is added to T)
                      
                      The instantaneous temperature is calculated at the end of
                      every ionic move and BEFORE rescaling. This is the temperature
                      reported in the main output.
                      
                      For "delta_t" < 0, the actual average rate of heating or cooling
                      should be roughly C*delta_t/(nraise*dt) (C=1 for an
                      ideal gas, C=0.5 for a harmonic solid, theorem of energy
                      equipartition between all quadratic degrees of freedom).
      +--------------------------------------------------------------------
      
```
