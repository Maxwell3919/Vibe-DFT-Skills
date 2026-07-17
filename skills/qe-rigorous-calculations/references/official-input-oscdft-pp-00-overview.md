# INPUT_OSCDFT_PP — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_OSCDFT_PP.txt
- Retrieved: 2026-07-17T11:49:30+00:00
- Official source SHA-256: `377d16e04d80742e8da1a865b87d1012efc11e996d5de5869d0e0e964b3667c4`
- Extracted text SHA-256: `3bf469a99e5aa6393777d8e47d3f1dd136d1a5703c58feb0461ff8370f4d03c0`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:26 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: oscdft_pp.x / PWscf / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


Input data format: { } = optional, [ ] = it depends, | = or

Purpose of oscdft_pp.x:
This calculates the occupation numbers, eigenvectors, and matrices as a post-processing
program. REQUIRES the oscdft.in file in the same working directory as where the
oscdft_pp.x command is ran.

Structure of the input data:
===============================================================================

    &OSCDFT_PP_NAMELIST
      ...
    /



========================================================================
```
