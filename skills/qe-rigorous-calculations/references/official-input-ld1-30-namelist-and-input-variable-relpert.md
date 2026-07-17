# INPUT_LD1 — NAMELIST: &INPUT — Variable: relpert

- Official source: https://www.quantum-espresso.org/Doc/INPUT_LD1.txt
- Retrieved: 2026-07-17T11:49:17+00:00
- Official source SHA-256: `dcea0ae3ef68c1cf577f7920bf1572c02f6ccf08a582b6eb8f409150a0572522`
- Extracted text SHA-256: `0b84d6f132e16f7bc8c19c1fbaa11ae905f866bacebc94f566eaa8b20ebbfa9e`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       relpert
   
   Type:           LOGICAL
   Default:        .false.
   Description:    If .true. the relativistic corrections to the non-relativistic
                   Kohn-Sham energy levels ("rel"=0 .and. "lsd"=0) are computed using
                   first-order perturbation theory in all-electron calculations.
                   The corrections consist of the following terms:
                      E_vel: velocity (p^4) correction
                      E_Dar: Darwin term
                      E_S-O: spin-orbit coupling
                   The spin-orbit term vanishes for s-electron states and gives
                   rise to a splitting of (2*l+1)*E_S-O for the other states.
                   The separate contributions are printed only if verbosity='high'.
                   
                   Formulas and notation are based on the Herman-Skillman book:
                   F. Herman and S. Skillman, "Atomic Structure Calculations",
                   Prentice-Hall, Inc., Englewood Cliffs, New Jersey, 1963
   +--------------------------------------------------------------------
   
```
