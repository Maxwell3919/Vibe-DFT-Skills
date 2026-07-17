# INPUT_EELS — NAMELIST: &LR_CONTROL — Variable: approximation

- Official source: https://www.quantum-espresso.org/Doc/INPUT_EELS.txt
- Retrieved: 2026-07-17T11:49:13+00:00
- Official source SHA-256: `c884578523001dc82364d82882329e7743ca966c353a3e21c94684a4be8f9e54`
- Extracted text SHA-256: `22800cb04a1f5c534bdcba5c8899fcee6ed445e1ccfea182b636457b2e792b67`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:24 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       approximation
   
   Type:           CHARACTER
   Default:        'TDDFT'
   Description:   
                   A string describing a level of theory:
    
                   'TDDFT' :
                        Time-Dependent Local Density Approximation or
                        Time-Dependent Generalized Gradient Approximation
                        (depending on the XC functional)
    
                   'IPA' :
                        Independent Particle Approximation (IPA)
    
                   'RPA_with_CLFE' :
                        Random Phase Approximation (RPA) with
                        Crystal Local Field Effects (CLFE)
   +--------------------------------------------------------------------
   
   +--------------------------------------------------------------------
   Variables:      q1, q2, q3
   
   Type:           REAL
   Default:        1.0, 1.0, 1.0
   Description:    The values of the transferred momentum q = (q1, q2, q3)
                   in Cartesian coordinates in units of 2pi/a, where
                   "a" is the lattice parameter.
   +--------------------------------------------------------------------
   
```
