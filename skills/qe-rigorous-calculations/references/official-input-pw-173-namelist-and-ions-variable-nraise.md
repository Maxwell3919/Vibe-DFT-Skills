# INPUT_PW — NAMELIST: &IONS — Variable: nraise

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `aec2363d4a09fc6a84cfa817dc2a4ca2a6993e1be2bfd3a84c5a27cc86945643`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       nraise
      
      Type:           INTEGER
      Default:        1
      Description:    if "ion_temperature" == 'reduce-T' :
                             every "nraise" steps the instantaneous temperature is
                             reduced by -"delta_t" (i.e. "delta_t" is added to the temperature)
                      
                      if "ion_temperature" == 'rescale-v' :
                             every "nraise" steps the average temperature, computed from
                             the last "nraise" steps, is rescaled to "tempw"
                      
                      if "ion_temperature" == 'rescaling' and "calculation" == 'vc-md' :
                             every "nraise" steps the instantaneous temperature
                             is rescaled to "tempw"
                      
                      if "ion_temperature" == 'berendsen' :
                             the "rise time" parameter is given in units of the time step:
                             tau = nraise*dt, so dt/tau = 1/nraise
                      
                      if "ion_temperature" == 'andersen' :
                             the "collision frequency" parameter is given as nu=1/tau
                             defined above, so nu*dt = 1/nraise
                      
                      if "ion_temperature" == 'svr' :
                             the "characteristic time" of the thermostat is set to
                             tau = nraise*dt
      +--------------------------------------------------------------------
      
```
