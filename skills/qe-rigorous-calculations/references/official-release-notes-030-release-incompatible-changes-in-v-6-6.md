# Quantum ESPRESSO release notes — Incompatible changes in v.6.6:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `d86d5035b17fe995699467ab8a78f4d81ea7777fe6eae86210bc482fd0065642`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Incompatible changes in v.6.6:
  * If no starting magnetization is set in a non-collinear or spin-orbit
    calculation, the magnetization is set to zero and remains zero.
    Previously, the magnetization was zero in practise (although numerical
    noise could lead to nonzero values) but was not forced to be zero.
  * Default value of parameter "diago_david_ndim" changed to 2:
    uses less RAM, execution time sometimes shorter, sometimes longer.
  * Grouping of inlc values into ranges for different developments.
    WARNING: inlc for rVV10 has been changed to inlc=26.
  * Conversion from 1D FFT real-space index to 3D positions moved into a
    small routine for all cases where such conversion is used
  * CP: atomic positions are now in array tau(1:3,1:nat), information on the
    type of atom is in array ityp(:). The logic is now the same as for all
    other codes and there is no need to re-order atoms or to put ultrasoft
    pseudopotentials first, non-conserving second.
  * Calls to LAXlib routines changed: module to be included replaced by file
    'laxlib.fh', descriptors replaced by integer values
  * Interpolation table for Q(G) is in a.u. and no longer in 2pi/a units
  * Part of pseudopotential-related code moved to new directory upflib/ and
    into library libupf.a. Directory upftools/ is obsolescent.
```
