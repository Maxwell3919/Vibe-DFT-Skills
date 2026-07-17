# INPUT_kcw — NAMELIST: &WANNIER — Variable: alpha_mix(niter)

- Official source: https://www.quantum-espresso.org/Doc/INPUT_kcw.txt
- Retrieved: 2026-07-17T11:49:55+00:00
- Official source SHA-256: `0e051e12dbf1f904e8044c5f2fc1f44a8e2f8f72f29e687d4fd675364d26e3d0`
- Extracted text SHA-256: `a133409834e268ba3d866bc2f9a4d10aa79986324e62ad2f296daa8b80b75f43`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       alpha_mix(niter)
   
   Type:           REAL
   Default:        alpha_mix(1)=0.7
   Description:    Mixing factor (for each iteration) for updating
                   the scf potential:
                   
                   vnew(in) = alpha_mix*vold(out) + (1-alpha_mix)*vold(in)
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


========================================================================
```
