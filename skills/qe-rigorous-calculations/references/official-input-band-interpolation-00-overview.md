# INPUT_BAND_INTERPOLATION — Overview and input structure

- Official source: https://www.quantum-espresso.org/Doc/INPUT_BAND_INTERPOLATION.txt
- Retrieved: 2026-07-17T11:48:56+00:00
- Official source SHA-256: `b60e3891af78fc24ae40985e172e19ff674772d57eebe438f62dfd9a1e7a331f`
- Extracted text SHA-256: `d13a0350c9f17a55d9b382b0a4fb8b77d1161cf0bb34db26b4cf0a32171eedba`
- Official Last-Modified: Tue, 11 Nov 2025 16:29:37 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
*** FILE AUTOMATICALLY CREATED: DO NOT EDIT, CHANGES WILL BE LOST ***

------------------------------------------------------------------------
INPUT FILE DESCRIPTION

Program: band_interpolation.x / PWscf / Quantum ESPRESSO (version: 7.5)
------------------------------------------------------------------------


Purpose of band_interpolation.x:
  This contains four band energies interpolation methods,
  to be advantageously (but not necessarly) used for EXX band structure computations.

  The PP/src/band_interpolation.x post-processing subprogram reads the band energies
  stored in the pwscf.xml file after an SCF calculation on a uniform Monkhorst-Pack grid,
  and interpolates the eigenvalues to an arbitrary set of k-points provided in input.

  The workflow is just:

        (1) do an SCF on a uniform grid
        (2) call the interpolator from the folder in which the pwscf.xml
             file is present (band_interpolation.x < input)

  For large EXX calculations the first step can be splitted in two substeps:

        (1) do an SCF calculation on a uniform grid with occupied bands only
        (2) do a NSCF (or Bands) calculation on the same uniform grid adding virtual orbitals
        (3) call the interpolator from the folder in which the pwscf.xml file is present

  Four interpolation methods have been included (see "method").

  The interpolated band structure in eV units is written in a file named [method].dat
  (e.g. fourier-diff.dat for the fourier-diff method) that is plottable with Grace or Gnuplot
  (e.g. xmgrace -nxy fourier-diff.dat)

Structure of the input data:
============================

   &INTERPOLATION
     ...
   /

   [ ROUGHNESS
        RoughN
        'automatic' or RoughC(1) RoughC(2) RoughC(3) ... RoughC(RoughN) ]

   [ USER_STARS
        NUser
        vec_X vec_Y vec_Z ]

   K_POINTS { tpiba_b }
      nks
      xk_x, xk_y, xk_z,  wk



========================================================================
```
