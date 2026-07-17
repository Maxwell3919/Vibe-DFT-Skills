# INPUT_OSCDFT — NAMELIST: &OSCDFT — Variable: constraint_conv_thr

- Official source: https://www.quantum-espresso.org/Doc/INPUT_OSCDFT.txt
- Retrieved: 2026-07-17T11:49:28+00:00
- Official source SHA-256: `e91edda1595da7b1c15244530b31ab9368e0fc0bad5146f74c1dcfeb21a95888`
- Extracted text SHA-256: `291278c0c8a8c079fac3045292120e6e4ae72d8190ac8c738de2d4453bfb289d`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       constraint_conv_thr
   
   Type:           DOUBLE
   Default:        5.0D-3
   Description:    Convergence threshold for the mean absolute error (MAE) computed
                   by averaging the absolute difference between the current and
                   target occupation matrices. When this threshold is reached,
                   the constarined is released.
   +--------------------------------------------------------------------
   
```
