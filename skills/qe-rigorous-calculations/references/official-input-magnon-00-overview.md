# INPUT_Magnon — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Magnon.txt
- Retrieved: 2026-07-17T11:49:24+00:00
- Official source SHA-256: `9d2ccecbe10a4b9f51519e86bb4361dec4c34509bf928d85f62328c09bbec0f1`
- Extracted text SHA-256: `b61ad49f88e144b9964644e02d375a3d858132dee1d2c56b738f9ded97b4a73b`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: turbo_magnon.x / turboMAGNON / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


    Input data format: { } = optional, [ ] = it depends.

All quantities whose dimensions are not explicitly specified are in
RYDBERG ATOMIC UNITS

BEWARE: TABS, DOS <CR><LF> CHARACTERS ARE POTENTIAL SOURCES OF TROUBLE

Comment lines in namelists can be introduced by a "!", exactly as in
fortran code. Comments lines in ``cards'' can be introduced by
either a "!" or a "#" character in the first position of a line.

Structure of the input data:
===============================================================================

&LR_INPUT
  ...
/

&LR_CONTROL
  ...
/



========================================================================
```
