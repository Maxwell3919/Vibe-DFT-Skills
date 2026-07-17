# INPUT_pw2gw — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_pw2gw.txt
- Retrieved: 2026-07-17T11:49:59+00:00
- Official source SHA-256: `262b3b212ffe093365b230f9b3fa6fff948648eab4455f2eb0ddab1fe87ac2ab`
- Extracted text SHA-256: `b51a2358826f1b7309b7eb1c8939fd698c83fb8cb03e592d0313916345a7cb4d`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: pw2gw.x / PWscf / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


Purpose of pw2gw.x:
   Optical properties in single-particle approach (Fermi Golden Rule).
   Interface with GW and excitonic codes.

   The code computes and writes ("matrixelements" file) the optical matrix elemenents in the
   dipole approximation.

   The code computes the imaginary part of the dielectric tensor xx, yy and zz ("epsX.dat", "epsY.dat",
   "epsZ.dat") and the average ("epsTOT.dat")

Structure of the input data:
============================

   &INPUTPP
     ...
   /



========================================================================
```
