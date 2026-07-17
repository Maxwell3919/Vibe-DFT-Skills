# Quantum ESPRESSO release notes — Fixed in version 4.0.2:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `18a8a7ae3b9c44b8c4acb72fc146ac1403542ef21ef7ecd182ee73b25327f9d3`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 4.0.2:

  * Nuclear masses not correctly displayed for variable-cell calculations
  * Probably all results for EFG (electric field gradients) were wrong,
    due to an incorrect multiplication of "r" with "alat" inside a loop
    (should have been outside: routine PW/ewald_dipole.f90)
  * Calculation with fixed magnetization and nspin=2 (using 2 fermi
    levels) was not working in v. 4.0.1
  * non linear core correction was not detected in FPMD run
  * effective charges + US PP + spin-orbit not correct in noncubic cases.
  * symm_type was not properly set by pw_restart (used in various 
    post-processing including phonons) when using free lattice 
    (ibrav=0) and symm_type=hexagonal.
  * CP: conjugate gradient had a bug in some cases of parallel 
    execution. Also: default max number of iterations was not
    what was promised in the documentation (100)
  * phonon: alpha_pv depended on the number of  unoccupied bands
    in insulators (harmless).
  * fpmd was using wrong forces propagate cell variables in
    variable-cell calculations. Also: interpolation tables
    were a little bit too small for variable cell simulation
    (not really a bug but it could be annoying)
  * Minor glitch in configure for pathscale compiler. Note that 
    in the machine that has been tested, compilation of iotk 
    fails for mysterious reasons if CPP = pathcc -E, while it
    works with CPP = /lib/cpp -P --traditional

                                * * * * *
```
