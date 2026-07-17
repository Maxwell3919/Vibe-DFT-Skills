# INPUT_Magnon — NAMELIST: &LR_CONTROL — Variable: ipol

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Magnon.txt
- Retrieved: 2026-07-17T11:49:24+00:00
- Official source SHA-256: `9d2ccecbe10a4b9f51519e86bb4361dec4c34509bf928d85f62328c09bbec0f1`
- Extracted text SHA-256: `90031f9e38eb9edfbc725b088a669c09c038f8f8258417c9e2fb982554912d61`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ipol
   
   Type:           INTEGER
   Default:        1
   Description:    An integer variable that determines which column of the
                   dynamical magnetic susceptibility will be computed:
                   1 -> chi_ax(omega), 2 -> chi_ay(omega), and
                   3 -> chi_az(omega), with a=(x,y,z). When set to 4,
                   three Lanczos chains are sequentially performed and the
                   full susceptibility tensor is computed.
   +--------------------------------------------------------------------
   
   +--------------------------------------------------------------------
   Variables:      q1, q2, q3
   
   Type:           REAL
   Default:        1.0, 1.0, 1.0
   Description:    The values of the transferred momentum q = (q1, q2, q3)
                   in Cartesian coordinates in units of 2pi/a, where
                   "a" is the lattice parameter.
   +--------------------------------------------------------------------
   
===END OF NAMELIST======================================================


This file has been created by helpdoc utility on Wed Sep 03 14:26:49 CEST 2025
```
