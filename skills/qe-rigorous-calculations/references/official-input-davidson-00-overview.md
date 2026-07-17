# INPUT_Davidson — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Davidson.txt
- Retrieved: 2026-07-17T11:49:12+00:00
- Official source SHA-256: `3119323bee658797174ac83c6f304a99ae95949a07ca87563de949ec1243341c`
- Extracted text SHA-256: `5ba26d228692e5f8a534396e480f76ea71fca63c0676fdb3bda323070ed0a280`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: turbo_davidson.x / turboTDDFPT / Quantum ESPRESSO (version: 7.5)
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

&LR_DAV
  ...
/



========================================================================
```
