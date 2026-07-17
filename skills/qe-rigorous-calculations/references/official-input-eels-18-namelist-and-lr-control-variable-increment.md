# INPUT_EELS — NAMELIST: &LR_CONTROL — Variable: increment

- Official source: https://www.quantum-espresso.org/Doc/INPUT_EELS.txt
- Retrieved: 2026-07-17T11:49:13+00:00
- Official source SHA-256: `c884578523001dc82364d82882329e7743ca966c353a3e21c94684a4be8f9e54`
- Extracted text SHA-256: `687832f50c99d87a469f485ddbfd2021a09c3a11fad4471c1685f0403f863202`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:24 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       increment
   
   Type:           REAL
   Default:        0.001
   See:            start, end
   Description:    This variable is used only when "calculator" = 'sternheimer'.
                   "increment" is an incremental step used to define the mesh
                   of frequencies between "start" and "end".
                   "increment" is specified in units controlled by "units".
   +--------------------------------------------------------------------
   
```
