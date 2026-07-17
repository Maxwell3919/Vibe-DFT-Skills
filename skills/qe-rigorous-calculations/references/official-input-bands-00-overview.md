# INPUT_BANDS — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_BANDS.txt
- Retrieved: 2026-07-17T11:48:54+00:00
- Official source SHA-256: `b8b1193c4f2723310151d7825240f9b20fe2212d1e0f509cce89988a93f7a14a`
- Extracted text SHA-256: `31486ef592ca6b92de4d69642b3f946b018ba667efb30d0e87955f67fb9cafe2`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: bands.x / PWscf / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


Purpose of bands.x:
   Re-order bands, computes band-related properties. Currently,
   re-ordering can be done with two different algorithms:
   (a) by maximising the overlap with bands at previous k-point
   (b) by computing symmetry properties of each wavefunction
   Bands-related properties that can be computed are currently
   (a) The expectation value of the spin operator on each spinor
       wave-function (noncolinear case only)
   (b) The expectation value of p

The input data can be read from standard input or from file using
command-line options "bands.x -i file-name" (same syntax as for pw.x)

Output files:
- file "filband" containing the band structure, in a format
  suitable for plotting code "plotband.x"
- file "filband".rap (if "lsym" is .t.)  with symmetry information,
  to be read by plotting code "plotband.x"
- if ("lsigma"(i)): file "filband".i, i=1,2,3, with expectation values
  of the spin operator in the noncolinear case
- file "filband".gnu with bands in eV, directly plottable using gnuplot
- file "filp" with matrix elements of p (including the nonlocal potential
  contribution i*m*[V_nl,x])

Structure of the input data:
============================

   &BANDS
     ...
   /



========================================================================
```
