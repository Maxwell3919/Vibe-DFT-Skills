# INPUT_PW — NAMELIST: &FCP — Variable: fcp_nraise

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `22683e10244aa72e84f6ad030128ad063e5c25f51e0346658f8052988c881f76`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       fcp_nraise
      
      Type:           INTEGER
      Default:        "nraise"
      Description:    if "fcp_temperature" == 'reduce-T' :
                             every "fcp_nraise" steps the instantaneous temperature is
                             reduced by -"fcp_delta_t" (i.e. "fcp_delta_t" is added to the temperature)
                      
                      if "fcp_temperature" == 'rescale-v' :
                             every "fcp_nraise" steps the average temperature, computed from
                             the last "fcp_nraise" steps, is rescaled to "fcp_tempw"
                      
                      if "fcp_temperature" == 'berendsen' :
                             the "rise time" parameter is given in units of the time step:
                             tau = fcp_nraise*dt, so dt/tau = 1/fcp_nraise
                      
                      if "fcp_temperature" == 'andersen' :
                             the "collision frequency" parameter is given as nu=1/tau
                             defined above, so nu*dt = 1/fcp_nraise
      +--------------------------------------------------------------------
      
   \\\---
   
```
