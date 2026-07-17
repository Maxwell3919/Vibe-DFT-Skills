# INPUT_OSCDFT — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_OSCDFT.txt
- Retrieved: 2026-07-17T11:49:28+00:00
- Official source SHA-256: `e91edda1595da7b1c15244530b31ab9368e0fc0bad5146f74c1dcfeb21a95888`
- Extracted text SHA-256: `603ccc60b49666c13533ce0d277b95821c881fbbc8cc8fd96c15861563669dfe`
- Official Last-Modified: Tue, 11 Nov 2025 16:32:09 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: pw.x with OS-CDFT / PWscf / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------



::::  ABOUT 

   OS-CDFT allows control of the oxidation state of a transition metal element by
   constraining the occupation numbers.
   For information on the method, see ""://doi.org/10.1021/acs.jctc.9b00281
   C. Ku, P. H. L. Sit, J. Chem. Theory Comput. 2019, 15, 9, 4781-4789
   


::::  COMPILATION 

   Using autoconf:
       ./configure ...
       nano make.inc # append -D__OSCDFT into DFLAGS = ... (or MANUAL_DFLAGS = ...)
       make pw pp ...
   
   Using cmake:
       cmake -DQE_ENABLE_OSCDFT=ON ... <path-to-qe-source>
       make pw pp ...
   


::::  USAGE 

   Requires oscdft.in file, described below, in the same directory as where the pw.x command is ran.
       pw.x -inp <input-file> -oscdft ...
   

Input data format: { } = optional, [ ] = it depends, | = or

Structure of the oscdft.in file:
===============================================================================

    &OSCDFT
      ...
    /

    TARGET_OCCUPATION_NUMBERS
      see "TARGET_OCCUPATION_NUMBERS"

    [ GAMMA_VAL
      gamma_val(1)
      ...
      gamma_val(n_oscdft) ]



========================================================================
```
