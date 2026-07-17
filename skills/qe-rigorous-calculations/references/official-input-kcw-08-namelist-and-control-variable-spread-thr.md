# INPUT_kcw — NAMELIST: &CONTROL — Variable: spread_thr

- Official source: https://www.quantum-espresso.org/Doc/INPUT_kcw.txt
- Retrieved: 2026-07-17T11:49:55+00:00
- Official source SHA-256: `0e051e12dbf1f904e8044c5f2fc1f44a8e2f8f72f29e687d4fd675364d26e3d0`
- Extracted text SHA-256: `2e9e632daba074d0605040d67bbec962e9d2841bf05aed1ff1d230437fa1e384`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       spread_thr
   
   Type:           REAL
   Default:        0.0001 Ry
   Description:    HARD-CODED FOR NOW. Two or more Wannier functions are considered
                   identical if their spread (self-hartree) differ by less than spread_thr.
                   Requires "check_spread" = .true.
   +--------------------------------------------------------------------
   
```
