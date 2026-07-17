# INPUT_Lanczos — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Lanczos.txt
- Retrieved: 2026-07-17T11:49:18+00:00
- Official source SHA-256: `58c02f4cb1fdefbef4203bbe55d16af2a768acd7cfb5462fc62bd1dfd07cb530`
- Extracted text SHA-256: `07db32adfb2663d3e1684e5f39ba5ff2f15e5ae05de1e4e45e59747653eceac5`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:46 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: turbo_lanczos.x / turboTDDFPT / Quantum ESPRESSO (version: 7.5)
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

[ &LR_POST
  ...
 / ]



========================================================================
```
