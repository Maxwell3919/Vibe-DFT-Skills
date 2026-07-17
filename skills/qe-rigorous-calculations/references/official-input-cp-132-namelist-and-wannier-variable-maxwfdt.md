# INPUT_CP — NAMELIST: &WANNIER — Variable: maxwfdt

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `0fe522de68f210d8925f9d4ca42c4731f18a4f9aa05543330052a11c0710f5f1`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       maxwfdt
   
   Type:           REAL
   Default:        0.3D0
   Description:    The maximum step size to take in the SD/CG direction
                   The code calculates an optimum step size, but that may be
                   either too small (takes forever to converge)  or too large
                   (code goes crazy) . This option keeps the step size between
                   wfdt and maxwfdt. In my experience 0.1 and 0.5 work quite
                   well. (but don't blame me if it doesn't work for you)
   +--------------------------------------------------------------------
   
```
