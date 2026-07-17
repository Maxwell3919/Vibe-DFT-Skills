# INPUT_CPPP — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CPPP.txt
- Retrieved: 2026-07-17T11:49:00+00:00
- Official source SHA-256: `9a1344351309e168957be343641bf7f2ffe66f2c597f8b5a14d2617f2f3e2d6b`
- Extracted text SHA-256: `7c3227c6454fc2dedcc0a1785eb486e2c8590d09095359ff4bc33efb7d741b31`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: cppp.x / CP / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


=============================================================================
                            CP Post-Processing code (cppp.x)
=============================================================================

The cppp.x code is an utility that can be used to extract data from the CP
restart and CP trajectory files.

INPUT:
=====

the program read the input parameters from the standard input or from
any other file specified through the usual "-input" command line flag.
The input parameters, in the input file, should be specified in the inputpp
namelist follow:

&INPUTPP
  ...
  cppp_input_parameter
  ...
/



========================================================================
```
