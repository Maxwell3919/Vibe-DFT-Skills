# INPUT_D3HESS — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_D3HESS.txt
- Retrieved: 2026-07-17T11:49:07+00:00
- Official source SHA-256: `2f2fd644c6b39496b093a9942534fbc04524ec3e174001e26c1a276e510bd788`
- Extracted text SHA-256: `ee5d3b4f69e5e973d3b8bc8a33e765f6f5284889855447107c09bfc6dcd364b1`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: d3hess.x / PWscf / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


Purpose of d3hess.x:
  This is a post processing program to compute second derivatives of D3 dispersion in QE.

  The d3hess.x program should be run after an scf or relax calculation.
  It reads the molecular geometry from the xml file in the outdir and save
  the second derivatives matrix in a file on the disk.
  Afterwords, phonon reads the file and add the D3 Hessian matrix to the dynamical matrix with the proper phase (q),
  to include dispersion effects on vibrational frequencies.

  The workflow is just:

        (1) do an SCF
        (2) run d3hess
        (3) run phonon

  Please note that filhess in d3hess input and dftd3_hess in phonon input, if given, should match.
  Please also note that second derivatives of the three-body term of d3 dispersion are not implemented,
  and phonon calculations with d3 should be run with dftd3_threebody=.false. in the SCF.

Structure of the input data:
============================

   &INPUT
     ...
   /



========================================================================
```
