# INPUT_kcw — NAMELIST: &HAM — Variable: use_ws_distance

- Official source: https://www.quantum-espresso.org/Doc/INPUT_kcw.txt
- Retrieved: 2026-07-17T11:49:55+00:00
- Official source SHA-256: `0e051e12dbf1f904e8044c5f2fc1f44a8e2f8f72f29e687d4fd675364d26e3d0`
- Extracted text SHA-256: `c27d215237a27b8a1bc45cb9df32b1bfbda4c6b0a3f6a4bb156a2010831d351d`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       use_ws_distance
   
   Type:           LOGICAL
   Default:        .TRUE.
   Description:    If .true. the position of the Wannier function inside the cell is used
                   to set the proper distance and to have a smoother interpolation. Requires
                   seedname_centres.xyz to be printed by the previous Wannier90 run. If the
                   file is not found it is automatically switched to .FALSE. and only the
                   distance between the cells is used (see also Wannier90 documentation)
   +--------------------------------------------------------------------
   
```
