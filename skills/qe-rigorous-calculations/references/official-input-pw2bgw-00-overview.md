# INPUT_pw2bgw — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_pw2bgw.txt
- Retrieved: 2026-07-17T11:49:58+00:00
- Official source SHA-256: `5f52150cf5d567429fbca7663ea1ecd3841683947b6ecfd410873e0a6d134e55`
- Extracted text SHA-256: `e0c1b3e5692ca754f6c3f03a4f2170e28a61ab6b2211090334cf4df0ae5f5d44`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:01 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: pw2bgw.x / PWscf / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


Purpose of pw2bgw.x:
   Converts the output files produced by pw.x to the input files for BerkeleyGW.

You cannot use USPP, PAW, or spinors in a pw.x run for BerkeleyGW.

You cannot use "K_POINTS gamma" in a pw.x run for BerkeleyGW.
Use "K_POINTS { tpiba | automatic | crystal }" even for the
Gamma-point calculation.

It is recommended to run a pw.x "bands" calculation with "K_POINTS crystal"
and a list of k-points produced by kgrid.x, which is a part of BerkeleyGW
package (see BerkeleyGW documentation for details).

You can also run a pw.x "nscf" calculation instead of "bands", but in this
case pw.x may generate more k-points than provided in the input file of pw.x.
If this is the case for your calculation you will get errors in BerkeleyGW.

Examples showing how to run BerkeleyGW on top of Quantum ESPRESSO including
the input files for pw.x and pw2bgw.x are distributed together with the
BerkeleyGW package.

Structure of the input data:
============================

   &INPUT_PW2BGW
     ...
   /



========================================================================
```
