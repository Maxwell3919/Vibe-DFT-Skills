# INPUT_OSCDFT — NAMELIST: &OSCDFT — Variable: convergence_type

- Official source: https://www.quantum-espresso.org/Doc/INPUT_OSCDFT.txt
- Retrieved: 2026-07-17T11:49:28+00:00
- Official source SHA-256: `e91edda1595da7b1c15244530b31ab9368e0fc0bad5146f74c1dcfeb21a95888`
- Extracted text SHA-256: `0119217f7a037191554fb7392acf52bc05e7681ed16c58d61ab5fe8b8cd27692`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       convergence_type
   
   Type:           CHARACTER
   Default:        'gradient'
   Description:   
                   The variable that is checked for convergence with the convergence threshold.
    
                   'multipliers' :
                        Converges when the change in multipliers between iterations
                        is less than the threshold.
    
                   'gradient' :
                        Converges when (occupation number - target occupation number)
                        is less than the threshold.
    
                   'energy' :
                        Converges when the change in total energy between iterations
                        is less than the threshold.
    
                   'always_false' :
                        Never converges (for debugging).
    
                   'always_true' :
                        Always converges (for debugging).
   +--------------------------------------------------------------------
   
```
