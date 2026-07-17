# INPUT_OSCDFT — NAMELIST: &OSCDFT — Variable: array_convergence_func

- Official source: https://www.quantum-espresso.org/Doc/INPUT_OSCDFT.txt
- Retrieved: 2026-07-17T11:49:28+00:00
- Official source SHA-256: `e91edda1595da7b1c15244530b31ab9368e0fc0bad5146f74c1dcfeb21a95888`
- Extracted text SHA-256: `6ece894fab5c6fcebb233349d9009415ef724f894bef2e73eaf5f6fbb9eb9510`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       array_convergence_func
   
   Type:           CHARACTER
   Default:        'maxval'
   Description:   
                   Specify the method of multiple values to scalar for convergence test
                   when "convergence_type" is either 'gradient' or 'multipliers'.
    
                   'maxval' :
                        Takes the maximum of the "convergence_type" before comparing with
                        threshold.
    
                   'norm' :
                        Takes the root sum squared of the "convergence_type" before
                        comparing with threshold.
    
                   'rms' :
                        Takes the root mean squared of the "convergence_type" before
                        comparing with threshold.
   +--------------------------------------------------------------------
   
```
