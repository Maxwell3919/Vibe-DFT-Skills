# INPUT_EELS — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_EELS.txt
- Retrieved: 2026-07-17T11:49:13+00:00
- Official source SHA-256: `c884578523001dc82364d82882329e7743ca966c353a3e21c94684a4be8f9e54`
- Extracted text SHA-256: `a5d4942e06ccfb55693efd2e3b7cd225e30ad40116498224a92e1e00041af959`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:24 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: turbo_eels.x / turboEELS / Quantum ESPRESSO (version: 7.5)
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
