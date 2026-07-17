# INPUT_CP — NAMELIST: &SYSTEM — Variable: q2sigma

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `32b1a3d6d3d000eab0d84cce7c4007e8e20e2a0a2d08ebc63bff3d3dffa1d532`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       q2sigma
   
   Type:           REAL
   Default:        0.1
   Description:    ecfixed, qcutz, q2sigma:  parameters for modified functional to be
                   used in variable-cell molecular dynamics (or in stress calculation).
                   "ecfixed" is the value (in Rydberg) of the constant-cutoff;
                   "qcutz" and "q2sigma" are the height and the width (in Rydberg)
                   of the energy step for reciprocal vectors whose square modulus
                   is greater than "ecfixed". In the kinetic energy, G^2 is
                   replaced by G^2 + qcutz * (1 + erf ( (G^2 - ecfixed)/q2sigma) )
                   See: M. Bernasconi et al, J. Phys. Chem. Solids 56, 501 (1995)
   +--------------------------------------------------------------------
   
```
