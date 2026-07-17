# INPUT_kcw — NAMELIST: &WANNIER — Variable: seedname

- Official source: https://www.quantum-espresso.org/Doc/INPUT_kcw.txt
- Retrieved: 2026-07-17T11:49:55+00:00
- Official source SHA-256: `0e051e12dbf1f904e8044c5f2fc1f44a8e2f8f72f29e687d4fd675364d26e3d0`
- Extracted text SHA-256: `1ae436f61b43b8e6b6094420468da6c2f8851aa55d93fa57f1c62ac88e0262af`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       seedname
   
   Type:           CHARACTER
   Default:        wann
   Description:    The seedname of the previous Wannier90 calculation for occupied states.
                   NOTA BENE: the code implicitely assumed that the seedname for empty
                   state is the same as that for occupied state with "_emp" appended.
                   Keep this in mind when set up the wannier90 inputs.
                   
                   For example:
                   wann.win         is the wannier90 input file for the occupied states.
                   wann_emp.win     is the wannier90 input file for the empty states.
   +--------------------------------------------------------------------
   
```
