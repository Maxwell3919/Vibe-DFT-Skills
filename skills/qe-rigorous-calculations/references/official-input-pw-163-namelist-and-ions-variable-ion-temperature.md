# INPUT_PW — NAMELIST: &IONS — Variable: ion_temperature

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `c9f170faae8e454c778de27ed6eda2db0a96f51d7cb0d2fa39438c54aabafc47`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
      +--------------------------------------------------------------------
      Variable:       ion_temperature
      
      Type:           CHARACTER
      Default:        'not_controlled'
      Description:   
                      Available options are:
       
                      'rescaling' :
                           control ionic temperature via velocity rescaling
                           (first method) see parameters "tempw", "tolp", and
                           "nraise" (for VC-MD only).
       
                      'rescale-v' :
                           control ionic temperature via velocity rescaling
                           (second method) see parameters "tempw" and "nraise"
       
                      'rescale-T' :
                           scale temperature of the thermostat every "nraise" steps
                           by "delta_t", starting from "tempw".
                           The temperature is controlled via velocitiy rescaling.
       
                      'reduce-T' :
                           reduce temperature of the thermostat every "nraise" steps
                           by the (negative) value "delta_t", starting from "tempw".
                           If  "delta_t" is positive, the target temperature is augmented.
                           The temperature is controlled via velocitiy rescaling.
       
                      'nose' :
                           control ionic temperature using Nose-Hoover
                           thermostat. See also parameters "fnosep" , "tempw" ,
                           "nhpcl", "ndega" , "nhptyp"
       
                      'berendsen' :
                           control ionic temperature using "soft" velocity
                           rescaling - see parameters "tempw" and "nraise"
       
                      'andersen' :
                           control ionic temperature using Andersen thermostat
                           see parameters "tempw" and "nraise"
       
                      'svr' :
                           control ionic temperature using stochastic-velocity rescaling
                           (Donadio, Bussi, Parrinello, J. Chem. Phys. 126, 014101, 2007),
                           with parameters "tempw" and "nraise".
       
                      'initial' :
                           initialize ion velocities to temperature "tempw"
                           and leave uncontrolled further on
       
                      'not_controlled' :
                           (default) ionic temperature is not controlled
      +--------------------------------------------------------------------
      
```
