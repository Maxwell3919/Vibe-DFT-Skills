# INPUT_molecularpdos — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_molecularpdos.txt
- Retrieved: 2026-07-17T11:49:57+00:00
- Official source SHA-256: `1e47fd2282c196dd8cfeb4de49502cedcb2fd40960784dcdc8b6955a6175cd8d`
- Extracted text SHA-256: `021f8a6c8457d1b7456687df4b3cf4256cdf471a5b8db72d12488cc9fcdf0788`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:08 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: molecularpdos.x / PWscf / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


Purpose of molecularpdos.x:
    Takes the projections onto orthogonalized atomic wavefunctions
    as computed by projwfc.x (see outdir/prefix.save/atomic_proj.xml)
    to build an LCAO-like representation of the eigenvalues of a system
    "full" and "part" of it (each should provide its own atomic_proj.xml file).
    Then the eigenvectors of the full system are projected onto the ones
    of the part. For example, to decompose the PDOS of an adsorbed molecule
    into its molecular orbital, as determined by a gas-phase calculation.

Reference:
    An explanation of the keywords and the implementation
    is provided in Scientific Reports | 6:24603 (2016)
    DOI: 10.1038/srep24603 (Supp. Info).


Structure of the input data:
============================

   &INPUTMOPDOS
     ...
   /



========================================================================
```
