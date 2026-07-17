# INPUT_OSCDFT — NAMELIST: &OSCDFT — Variable: final_conv_thr

- Official source: https://www.quantum-espresso.org/Doc/INPUT_OSCDFT.txt
- Retrieved: 2026-07-17T11:49:28+00:00
- Official source SHA-256: `e91edda1595da7b1c15244530b31ab9368e0fc0bad5146f74c1dcfeb21a95888`
- Extracted text SHA-256: `64a79472052837c626d0e42888aac879678a50504f2836117da388274cb1a49e`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       final_conv_thr
   
   Type:           DOUBLE
   Default:        -1.D0
   Description:    If "iteration_type" is 0 and "final_conv_thr" > 0.D0, the charge density
                   convergence is prevented when the OS-CDFT convergence test is
                   larger than "final_conv_thr". Otherwise, this is ignored.
   +--------------------------------------------------------------------
   
```
