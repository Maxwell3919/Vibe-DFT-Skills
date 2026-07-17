# Quantum ESPRESSO release notes — Fixed in version 3.2.1-3.2.3:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `b59705826fa5d195bbac6177ae79d6a13835f18fbb9e2e939a6d30b440392cfc`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 3.2.1-3.2.3:

  * CP in parallel execution had a serious bug if the third dimension
    of FFT arrays (nr3x/nr3sx) was not the same as FFT order (nr3/nr3s)
  * restart of pw.x in parallel could go bananas under some not-so-unusual
    circumstances, due to bad setting of a variable
  * various phonon glitches: pools and lsda, pools and dispersions,
    option lnscf, were not working
  * incorrect exchange-correlation contribution to the electro-optical 
    coefficient
  * check for stop condition was unsafe with pools and could hang pw.x
  * fixed occupations in parallel: array not allocated on all processors
  * Yet another problem of poor accuracy of routines calculating spherical 
    bessel functions - harmless except in some cases of pseudopotential 
    generation 
  * DOS EOF characters present in some files could cause trouble
    during installation
  * restart in phonon calculations was not always properly working
  * possible divide-by-zero error in dV_xc/dz (spin polarized case)
  * gamma_gamma symmetry was not working for open-shell molecules
  * T_h group not correctly identified in postprocessing
  * missing initialization of rho could lead to serious trouble
    if the physical and true dimensions of FFT grid did not coincide
  * Ewald real-space term could have been incorrectly calculated 
    if an atom was far away from the unit cell
  * Some variables were used before they were initialized - this could
    lead to crashes or unpredictable behaviour on some machines
  * lattice parameters a,b,c,cosab,cosac,cosbc were not properly 
    copied to the celldm in the case of triclinic lattice

                                 * * * * *
```
