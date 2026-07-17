# INPUT_PPRISM — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PPRISM.txt
- Retrieved: 2026-07-17T11:49:43+00:00
- Official source SHA-256: `1d61e61afd2d7e18ebc142a14dce2fde77900f0c4f606eb5fc0f0acb89d15d20`
- Extracted text SHA-256: `06b26b8d166765e71743d13b521165a02e5c68973920d01bd8aaf602b8da1175`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:01 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: pprism.x / PWscf / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


Purpose of pprism.x: data analysis and plotting for 3D-RISM or Laue-RISM.

The code performs two steps:

(1) reads the output file produced by pw.x, extract and calculate
    solvent's quantities (solvent charge, solvent potential, ...)

(2) writes solvent's quantities to file in a suitable format for
    various types of plotting and various plotting programs

The input data of this program is read from standard input
or from file and has the following format:

NAMELIST &INPUTPP
   containing the variables for step (1), followed by

NAMELIST &PLOT
   containing the variables for step (2)

The two steps can be performed independently. In order to perform
only step (2), leave namelist &INPUTPP blank. In order to perform
only step (1), do not specify namelist &PLOT

Intermediate results from step 1 can be saved to disk (see
variable "filplot" in &INPUTPP) and later read in step 2.
Since the file with intermediate results is formatted, it
can be safely transferred to a different machine.

All output quantities are in ATOMIC (RYDBERG) UNITS unless
otherwise explicitly specified.



========================================================================
```
