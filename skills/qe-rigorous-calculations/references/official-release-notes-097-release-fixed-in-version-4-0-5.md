# Quantum ESPRESSO release notes — Fixed in version 4.0.5:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `d9eb093ff41335543f07c1b019072e7770ad5c2264aeedf5dec40dab78c294e0`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 4.0.5:

  * option calwf=1 (CP with Wannier functions) was not working
  * more problems in symmetry analysis in special cases for C_4h and
    D_2h symmetry
  * various small memory leaks or double allocations in special cases
  * problem with effective charges d Force / d E in the non-collinear+NLCC case
  * calculation of ionic dipole, used for calculations with sawtooth 
    potential, used wrong reference point assuming the field parallel
    to z axis (while it can be parallel to any reciprocal basis vector). 
    All relax calculation in non-orthorhombic cells, and all calculations
    with option tefield and edir/=3, were completely wrong. Non-relax 
    calculation in the same cathegory were correct, apart from a constant, 
    but system-dependent, addictive factor in total energy.
  * generation of supercells in matdyn was not working (since a long time)
  * PWCOND: two more small bug fixed (in CVS since june)

                                * * * * *
```
