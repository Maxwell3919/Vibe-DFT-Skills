# INPUT_OSCDFT — NAMELIST: &OSCDFT — Variable: iteration_type

- Official source: https://www.quantum-espresso.org/Doc/INPUT_OSCDFT.txt
- Retrieved: 2026-07-17T11:49:28+00:00
- Official source SHA-256: `e91edda1595da7b1c15244530b31ab9368e0fc0bad5146f74c1dcfeb21a95888`
- Extracted text SHA-256: `ed049bb99fe34b967f1cee21de3c1f8a66e4071d3bf8f49d64b8dc1e60071e0f`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       iteration_type
   
   Type:           INTEGER
   Status:         REQUIRED
   Description:   
                   Order of charge density and OS-CDFT multipliers optimizations.
    
                   0 :
                        OS-CDFT multipliers optimization is a micro-iteration inside
                        the charge density iteration. The convergence threshold of the
                        OS-CDFT multipliers iterations can be set to start loose at
                        "max_conv_thr" and gradually tighten to a minimum of "min_conv_thr"
                        by multiplying the threshold with "conv_thr_multiplier" after
                        every successful OS-CDFT multipliers iteration. A final
                        convergence threshold of "final_conv_thr" can also be set
                        to prevent the charge density iteration from converging when
                        the OS-CDFT convergence test is larger than "final_conv_thr".
    
                   1 :
                        Charge density optimization is a micro-iteration inside the
                        OS-CDFT multiplier optimization. The convergence threshold of
                        the OS-CDFT multipliers is set by "max_conv_thr".
                        "min_conv_thr", "conv_thr_multiplier", and "final_conv_thr" are
                        ignored.
   +--------------------------------------------------------------------
   
```
