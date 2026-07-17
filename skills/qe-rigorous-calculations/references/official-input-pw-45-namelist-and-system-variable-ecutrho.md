# INPUT_PW — NAMELIST: &SYSTEM — Variable: ecutrho

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `e7761e802056ec19a59cf82e4524018afdc9b9039d4cbda56d68be7671affe36`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ecutrho
   
   Type:           REAL
   Default:        4 * "ecutwfc"
   Description:    Kinetic energy cutoff (Ry) for charge density and potential
                   For norm-conserving pseudopotential you should stick to the
                   default value, you can reduce it by a little but it will
                   introduce noise especially on forces and stress.
                   If there are ultrasoft PP, a larger value than the default is
                   often desirable (ecutrho = 8 to 12 times "ecutwfc", typically).
                   PAW datasets can often be used at 4*"ecutwfc", but it depends
                   on the shape of augmentation charge: testing is mandatory.
                   The use of gradient-corrected functional, especially in cells
                   with vacuum, or for pseudopotential without non-linear core
                   correction, usually requires an higher values of ecutrho
                   to be accurately converged.
   +--------------------------------------------------------------------
   
```
