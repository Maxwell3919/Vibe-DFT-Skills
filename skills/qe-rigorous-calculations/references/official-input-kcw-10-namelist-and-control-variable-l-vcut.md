# INPUT_kcw — NAMELIST: &CONTROL — Variable: l_vcut

- Official source: https://www.quantum-espresso.org/Doc/INPUT_kcw.txt
- Retrieved: 2026-07-17T11:49:55+00:00
- Official source SHA-256: `0e051e12dbf1f904e8044c5f2fc1f44a8e2f8f72f29e687d4fd675364d26e3d0`
- Extracted text SHA-256: `6072e0a71bcfd1c4d3c35fe7f3342de1344ec4ba84534a1a50b2eb6c4034c3c7`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       l_vcut
   
   Type:           LOGICAL
   Default:        FALSE
   Description:    If .TRUE. the Gygi-Baldereschi scheme is used to deal with
                   the q->0 divergence of the Coulomb integral (bare and screened).
                   Improves the convergence wrt k/q-point sampling.
                   Requires to correctly set "eps_inf" for the calculation of
                   the screened interaction.
                   
                   Use it only for periodic system.
                   For isoleted system use "assume_isolated", instead.
   +--------------------------------------------------------------------
   
```
