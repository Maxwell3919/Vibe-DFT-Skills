# INPUT_OSCDFT — NAMELIST: &OSCDFT — Variable: optimization_method

- Official source: https://www.quantum-espresso.org/Doc/INPUT_OSCDFT.txt
- Retrieved: 2026-07-17T11:49:28+00:00
- Official source SHA-256: `e91edda1595da7b1c15244530b31ab9368e0fc0bad5146f74c1dcfeb21a95888`
- Extracted text SHA-256: `b16bcd77464778eee30b33da2a8b2612b1d9783d955e3c0e0a9494f5456239bb`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       optimization_method
   
   Type:           CHARACTER
   Default:        'gradient descent'
   Description:   
                   Method to update the OS-CDFT multipliers.
    
                   'gradient descent'  :
                        multipliers -= "min_gamma_n"
                                       * (occupation number - target occupation number)
    
                   'gradient descent2'  :
                        multipliers -= "gamma_val" * "min_gamma_n"
                                       * (occupation number - target occupation number)
   +--------------------------------------------------------------------
   
```
