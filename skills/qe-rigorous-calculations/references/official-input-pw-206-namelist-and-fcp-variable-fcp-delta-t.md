# INPUT_PW — NAMELIST: &FCP — Variable: fcp_delta_t

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `58bf4355e3b9e98c83e21fc7db69a5b2aee12724329942025729bc0e1fa3e56e`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       fcp_delta_t
      
      Type:           REAL
      Default:        "delta_t"
      Description:    if "fcp_temperature" == 'rescale-T' :
                             at each step the instantaneous temperature is multiplied
                             by fcp_delta_t; this is done rescaling all the velocities.
                      
                      if "fcp_temperature" == 'reduce-T' :
                             every "fcp_nraise" steps the instantaneous temperature is
                             reduced by -"fcp_delta_t" (i.e. "fcp_delta_t" < 0 is added to T)
                      
                      The instantaneous temperature is calculated at the end of
                      FCP's move and BEFORE rescaling. This is the temperature
                      reported in the main output.
                      
                      For "fcp_delta_t" < 0, the actual average rate of heating or cooling
                      should be roughly C*fcp_delta_t/(fcp_nraise*dt) (C=1 for an
                      ideal gas, C=0.5 for a harmonic solid, theorem of energy
                      equipartition between all quadratic degrees of freedom).
      +--------------------------------------------------------------------
      
```
