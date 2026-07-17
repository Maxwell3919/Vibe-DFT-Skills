# INPUT_PW — NAMELIST: &FCP — Variable: fcp_temperature

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `48a37fea26b4989811dc26c3070184df451912f315ecb5d5f339ff7bde881d2f`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       fcp_temperature
      
      Type:           CHARACTER
      Default:        "ion_temperature"
      Description:   
                      Available options are:
       
                      'rescaling' :
                           control FCP's temperature via velocity rescaling
                           (first method) see parameters "fpc_tempw" and "fcp_tolp".
       
                      'rescale-v' :
                           control FCP's temperature via velocity rescaling
                           (second method) see parameters "fcp_tempw" and "fcp_nraise"
       
                      'rescale-T' :
                           control FCP's temperature via velocity rescaling
                           (third method) see parameter "fcp_delta_t"
       
                      'reduce-T' :
                           reduce FCP's temperature every "fcp_nraise" steps
                           by the (negative) value "fcp_delta_t"
       
                      'berendsen' :
                           control FCP's temperature using "soft" velocity
                           rescaling - see parameters "fcp_tempw" and "fcp_nraise"
       
                      'andersen' :
                           control FCP's temperature using Andersen thermostat
                           see parameters "fcp_tempw" and "fcp_nraise"
       
                      'initial' :
                           initialize FCP's velocities to temperature "fcp_tempw"
                           and leave uncontrolled further on
       
                      'not_controlled' :
                           (default) FCP's temperature is not controlled
      +--------------------------------------------------------------------
      
```
