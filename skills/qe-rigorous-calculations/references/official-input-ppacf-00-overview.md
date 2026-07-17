# INPUT_PPACF — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PPACF.txt
- Retrieved: 2026-07-17T11:49:41+00:00
- Official source SHA-256: `ec18cfa677f3d5684e7176a867c5d56868b44758bd2d43678d4ee813e1ecfc39`
- Extracted text SHA-256: `36d1f40f8aabefff02669e9940f9383c7052f70556272335c8a38bc22c84529c`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:01 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: ppacf.x / PWscf / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


Purpose of ppacf.x:
ACF analysis and print files to track signatures of binding
(PRB 97, 085115 (2018)).

For an illustration of how to use this code to set hybrid mixing
value, please refer to JCP 148, 194115 (2018) doi: 10.1063/1.5012870.

The code reads the output produced by pw.x, extracts and calculates
$E_{c}^{nl}$, $T_{c}^{nl}$, $E_{c,\lambda}^{LDA}$, $E_{c,\lambda}^{nl}$,
$E_{xc,\lambda}$, $T_c^{LDA}$.
If "lfock" is set to .True., the code also computes the total Fock
exchange value.

With flag "code_num" = 2, the codes can read output produced by VASP.

With flag "lplot", the codes also out puts files containing spatial
variation in most of these quantities.


The input data of this program is read from standard input or from file
and has the following format:

Structure of the input data:
============================

&PPACF
...
/

Intermediate results can be saved to disk (see variable "lplot" in &PPACF)
and later read by pp.x.
Since the file with intermediate results is formatted, it can be safely
transferred to a different machine. This also allows plotting of a
linear combination (for instance, energy density differences) by saving
two intermediate files and combining them (see variables in &PLOT
from pp.x .)

All output quantities are in ATOMIC (RYDBERG) UNITS unless otherwise
explicitly specified.



========================================================================
```
