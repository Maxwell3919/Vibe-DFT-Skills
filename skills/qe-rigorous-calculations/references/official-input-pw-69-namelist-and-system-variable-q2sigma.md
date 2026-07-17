# INPUT_PW — NAMELIST: &SYSTEM — Variable: q2sigma

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `af6df8fe5da4762c03acfb47dc18cdb18e91e47fe97cdf339beb690fbd4cfff5`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
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
                   See: M. Bernasconi et al, J. Phys. Chem. Solids 56, 501 (1995),
                   doi:10.1016/0022-3697(94)00228-2
   +--------------------------------------------------------------------
   
```
