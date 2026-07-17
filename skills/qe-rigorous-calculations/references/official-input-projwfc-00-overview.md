# INPUT_PROJWFC — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PROJWFC.txt
- Retrieved: 2026-07-17T11:49:45+00:00
- Official source SHA-256: `2fe26603465c910cec30dd5da42fb157e6e9135b8d099e01130833232df8c01c`
- Extracted text SHA-256: `a59931d109911103750a840d730ee71c681fa453dcced5db4be0e5aa529b769b`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:04 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: projwfc.x / PWscf / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


Purpose of projwfc.x:
    projects wavefunctions onto orthogonalized atomic wavefunctions,
    calculates Lowdin charges, spilling parameter, projected DOS
    (separated into up and down components for LSDA). Alternatively:
    computes the local DOS(E) integrated in volumes given in input
    (see "tdosinboxes") or k-resolved DOS (see "kresolveddos").
    Atomic projections are written to file "atomic_proj.xml".

Structure of the input data:
============================

   &PROJWFC
     ...
   /



========================================================================
```
