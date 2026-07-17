# INPUT_bgw2pw — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_bgw2pw.txt
- Retrieved: 2026-07-17T11:49:53+00:00
- Official source SHA-256: `92de4f864f7177a3928883b2238d6f14bdb17bdb3b3422fe3a27235ffdd1ad5b`
- Extracted text SHA-256: `0a5be8b3919d2be0e0d03c03fdbe7ebb43d6a0f5b9f9dc0c2a4c42d40971a6d2`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: bgw2pw.x / PWscf / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


Purpose of bgw2pw.x:
   Converts BerkeleyGW WFN and RHO files to the format of pw.x.
   NO LONGER WORKING AFTER v.6.3.
   This can be useful, for example, if you generate the plane waves
   on top of the valence bands and want to diagonalize them in pw.x.
   Look at the documentation for SAPO code in BerkeleyGW for more information.

bgw2pw.x reads common parameters from file "prefix".save/data-file.xml and
writes files "prefix".save/charge-density.dat (charge density in R-space),
"prefix".save/gvectors.dat (G-vectors for charge density and potential),
"prefix".save/K$n/eigenval.xml (eigenvalues and occupations for nth k-point),
"prefix".save/K$n/evc.dat (wavefunctions in G-space for nth k-point), and
"prefix".save/K$n/gkvectors.dat (G-vectors for nth k-point).

bgw2pw.x doesn't modify file "prefix".save/data-file.xml so make changes to this
file manually (for example, you will need to change the number of bands if you
are using bgw2pw.x in conjunction with SAPO code in BerkeleyGW).

Structure of the input data:
============================

   &INPUT_BGW2PW
     ...
   /



========================================================================
```
