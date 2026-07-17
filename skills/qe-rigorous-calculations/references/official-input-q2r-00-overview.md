# INPUT_Q2R — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_Q2R.txt
- Retrieved: 2026-07-17T11:49:50+00:00
- Official source SHA-256: `d493ae0332d60c865e904223a7db8a6b426570c1a07032946e186c869d5ca4ea`
- Extracted text SHA-256: `de82e515da8219696241695dee7d60edfaaa3256ec79b68422f43cd7dd2ae76b`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: q2r.x / PHonon / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


Purpose of q2r.x:

It reads force constant matrices C(q) produced by the ph.x code
for a grid of q-points and calculates the corresponding set
of interatomic force constants (IFC), C(R)

Input data format: [ ] = it depends

Structure of the input data:
========================================================================

&INPUT
   ...specs of namelist variables...
/

[ nr1 nr2 nr3
  nfile
     file(1)
     file(2)
     ...
     file(nfile) ]



========================================================================
```
