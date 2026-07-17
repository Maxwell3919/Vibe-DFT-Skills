# INPUT_CP — NAMELIST: &ELECTRONS — Variable: tcg

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `4470f256a564aec6d75afb0de3b271bd2c975ef116a94199a13e824cb605f472`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       tcg
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    if .TRUE. perform a conjugate gradient minimization of the
                   electronic states for every ionic step.
                   It requires Gram-Schmidt orthogonalization of the electronic
                   states.
   +--------------------------------------------------------------------
   
```
