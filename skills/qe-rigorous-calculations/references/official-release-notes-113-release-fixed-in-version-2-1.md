# Quantum ESPRESSO release notes — Fixed in version 2.1:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `0ee49694b3425651a7866fe293389be65ef16a1315e584d3d41f829e1e504109`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 2.1:

  * various T3E compilation problems
  * cpmd2upf was yielding incorrect DFT if converting BLYP PPs
  * some variables not properly written and read in restart file
  * The value of gamma_only was not correctly set when restarting or
    reading from file with option __NEW_PUNCH enabled
  * Incorrect calculation of eloc in pw2casino
  * Two serious bugs in the local-TF screening :
    possible occurrence of division by zero (present since v1.2),
    wrong mixing of spin polarized systems
  * cpmd2upf failed with some files due to bad check
  * Intel compiler v.8: wavefunction files four times bigger than needed
  * compilation problems on some version of SGI compiler
  * non-collinear code was not working with insulators and nbnd > nelec/2
  * multiple writes to file in parallel execution when calculating
    electron-phonon coefficients
  * various bugs in LBFGS
  * NEB + LDA+U = crash
  * compilation problems with __NEW_PUNCH
  * planar average crashed if used with a cubic system
  * Gamma-only phonon code not working for Raman calculations
    in some cases
  * yet another bug in phonon and k-point parallelization when
    reading namelist (phq_readin)
  * options startingwfc and startingpot were ignored if restarting
    from a previous calculation
  * pw2casino interface didn't work properly in spin-polarized case
    and didn't use variable "outdir"
  * minor bug in pwtools/pwo2xsf.sh 
  * serious bug in the path interpolator
  * phonon, post_processing, various other auxiliary codes were
    not working with k-point parallelization (pools) due to 
    double call to init_pool

                                 * * * * *
```
