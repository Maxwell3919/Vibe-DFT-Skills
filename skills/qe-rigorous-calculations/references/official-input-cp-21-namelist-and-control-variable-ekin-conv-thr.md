# INPUT_CP — NAMELIST: &CONTROL — Variable: ekin_conv_thr

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `54cdf5b60035a1c0d60086aa8d5a56b02591302f9971aa531998ef1d145ea767`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ekin_conv_thr
   
   Type:           REAL
   Default:        1.0D-6
   Description:    convergence criterion for electron minimization:
                   convergence is achieved when "ekin < ekin_conv_thr".
                   See also etot_conv_thr - both criteria must be satisfied.
   +--------------------------------------------------------------------
   
```
