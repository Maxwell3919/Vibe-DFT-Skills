# INPUT_DYNMAT — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_DYNMAT.txt
- Retrieved: 2026-07-17T11:49:10+00:00
- Official source SHA-256: `4da654f7ed8ec6ceb5d38a4e470389b2fb414999eb5233e083ea454c2669470e`
- Extracted text SHA-256: `679b216563e4c5342a1272869ea872b9ba3056fe3a8998274c514a79b8a223e3`
- Official Last-Modified: Tue, 11 Nov 2025 16:31:24 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: dynmat.x / PHonon / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


Purpose of dynmat.x:

- reads a dynamical matrix file produced by the phonon code

- adds the non-analytical part (if Z* and epsilon are read from
  file), applies the chosen Acoustic Sum Rule (if q=0)

- diagonalise the dynamical matrix

- calculates IR and Raman cross sections (if Z* and Raman
  tensors are read from file, respectively)

- writes the results to files, both for inspection and for
  plotting


Structure of the input data:
========================================================================

&INPUT
   ...specs of namelist variables...
/



========================================================================
```
