# INPUT_kcw — NAMELIST: &SCREEN — Variable: check_spread

- Official source: https://www.quantum-espresso.org/Doc/INPUT_kcw.txt
- Retrieved: 2026-07-17T11:49:55+00:00
- Official source SHA-256: `0e051e12dbf1f904e8044c5f2fc1f44a8e2f8f72f29e687d4fd675364d26e3d0`
- Extracted text SHA-256: `508ad0daad01dd6b336677a9e9f63f95525ca71a5e59e458ed431d56ee237a96`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       check_spread
   
   Type:           LOGICAL
   Default:        .FALSE.
   Description:    If .TRUE. the spread (self-hartree) of the Wannier functions is
                   checked and used to decide whether two or more Wannier functions
                   can be considered "identical" or not. Two Wannier functions are
                   considered identical if their spread (self-hartree) differ by less
                   than 1e-4 Ry (Hard coded for now, see "spread_thr").
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


========================================================================
```
