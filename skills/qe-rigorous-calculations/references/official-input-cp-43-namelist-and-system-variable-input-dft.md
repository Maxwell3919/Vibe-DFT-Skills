# INPUT_CP — NAMELIST: &SYSTEM — Variable: input_dft

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `f627bb0dd72207fc848f327995588c04f24b9baa61297837711b662136f19584`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       input_dft
   
   Type:           CHARACTER
   Default:        read from pseudopotential files
   Description:    Exchange-correlation functional: eg 'PBE', 'BLYP' etc
                   See Modules/funct.f90 for allowed values.
                   Overrides the value read from pseudopotential files.
                   Use with care and if you know what you are doing!
                   
                   Use 'PBE0' to perform hybrid functional calculation using Wannier functions.
                   Allowed calculation: 'cp-wf' and 'vc-cp-wf'
                   See CP specific user manual for further guidance (or in CPV/Doc/user_guide.tex)
                   and examples in CPV/examples/EXX-wf-example.
                   Also see related keywords starting with exx_.
   +--------------------------------------------------------------------
   
```
