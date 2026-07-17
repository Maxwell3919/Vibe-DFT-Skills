# INPUT_kcw — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_kcw.txt
- Retrieved: 2026-07-17T11:49:55+00:00
- Official source SHA-256: `0e051e12dbf1f904e8044c5f2fc1f44a8e2f8f72f29e687d4fd675364d26e3d0`
- Extracted text SHA-256: `3c63ab7c5111d5bec3a803dd23a753f47fd61a32262eb3ca1d077c5c3ddbfebf`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: kcw.x / KCW / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


Input data format: { } = optional, [ ] = it depends, # = comment

Structure of the input data:
===============================================================================

&CONTROL
   ...
/

&WANNIER
   ...
/

&SCREEN
   ...
/

&HAM
   ...
/

K_POINTS { tpiba | automatic | crystal | gamma | tpiba_b | crystal_b | tpiba_c | crystal_c }
if (gamma)
   nothing to read
if (automatic)
   nk1, nk2, nk3, k1, k2, k3
if (not automatic)
   nks
   xk_x, xk_y, xk_z,  wk
if (tpipa_b or crystal_b in a 'bands' calculation) see Doc/brillouin_zones.pdf



========================================================================
```
