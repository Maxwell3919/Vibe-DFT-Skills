# INPUT_wannier2pw — NAMELIST: &INPUTPP — Variable: wan2hub(i)

- Official source: https://www.quantum-espresso.org/Doc/INPUT_wannier2pw.txt
- Retrieved: 2026-07-17T11:50:03+00:00
- Official source SHA-256: `5ebe5d8a42dbaf47d03e86a148f958584243bd68b976f32492185b6884563012`
- Extracted text SHA-256: `a1b56da26c4cf81f63c38b7c6cb0a16a6eb4efcbad8e21499565eb21de6aa6e5`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       wan2hub(i)
   
   Type:           LOGICAL
   Description:    Set wan2hub(i) to .true. for those Wannier functions (i) which you want to use
                   as a basis to build the Hubbard projectors for DFT+U calculations. Note that
                   the total number of selected Wannier functions must match the expected
                   number of basis functions (e.g. 5 for d states, 3 for p states, etc per atom).
                   In order to selected the Wannier functions, one has to inspect the output of
                   Wannier90 calculations and see in which oredr the Wannier functions were generated.
   Default:        .FALSE.
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


This file has been created by helpdoc utility on Wed Sep 03 14:29:01 CEST 2025
```
