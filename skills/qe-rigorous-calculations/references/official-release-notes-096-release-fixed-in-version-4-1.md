# Quantum ESPRESSO release notes — Fixed in version 4.1:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `e7fd8fbddf59257fed9a807a8cf474bd693689d3aa80f62ac4de034d67981060`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 4.1:

  * the sum of all nuclear forces is no longer forced to zero in 
    Car-Parrinello dynamics. Forcing them to zero was not completely
    correct -- only the sum of nuclear plus "electronic" forces should 
    be exactly zero -- and was causing loss of ergodicity in some cases. 
  * symmetry analysis for spin-orbit case: a few signs in the character 
    tables of C_3 and S_6 have been changed so that they agree with the
    Koster-Dimmock-Wheeler-Statz tables.
  * a problem in the plotting routine plotband.f90 could yield wrong
    band plots even when the symmetry classification was correct.  
  * serious bug in plotting code pp.x: all plots requiring Fourier space
    interpolation, i.e.: 1d, 2d, user-supplied 3d grid, spherical average,
    were yielding incorrect results if performed on data produced by pw.x
    (and cp.x) using Gamma-only option. Workaround introduced, but it works
    (around) only if the desired data is first saved to file, then plotted.
  * stop_run was not properly deleting files in the case of path calculations 
  * Coulomb pseudopotentials in UPF v.2 format were not working 
    (courtesy of Andrea Ferretti)
  * electron-phonon calculation on a uniform grid of q-points + 
    Delta Vscf and dynamical matrices read from file should be fine now:
    the Delta Vscf saved to file are no longer overwritten at each q-point.
    Also: the xml file written by pw.x is no longer overwritten by ph.x.
  * nasty problem with C routines receiving fortran strings as arguments.
    The way it was done may lead to stack corruption and all kinds of
    unexpected and mysterious problems under some circumstances.
    Now fortran strings are converted to integer arrays, that can be
    safely passed to C, and converted back in Modules/wrappers.f90
  * USPP generated with ld1.x may have been incorrectly written to
    UPF format v.2 in all 4.0.x versions . The error may have been
    small enough to go unnoticed but may be not negligible. All USPP
    in UPF format tagged as version 2.0.0 should be regenerated.

                                * * * * *
```
