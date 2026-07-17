# Quantum ESPRESSO release notes — Fixed in version 1.2.0 (f90):

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `c9dc33b622fd69561ccb6f640e40474ae94bdaaa2268c544a63033f15fb44acc`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in version 1.2.0 (f90):
  
  * dynmat.f90: out-of-bound error fixed
  * pplib/chdens.F90, pplib/projwave.F90 : compilation problems
    for alpha (found by Giovanni Cantele)
  * postprocessing routines: problems with unallocate pointers
    passed to subroutine plot_io fixed (found by various people)
  * postprocessing with ibrav=0 was not working properly
  * rather serious bug in cinitcgg (used by conjugate-gradient
    diagonalization) could produce mysterious crashes. The bug 
    appeared in version 1.1.1.
  * pplib/dos.f90 was not plotting the expected energy window
  * pplib/chdens.F90, pplib/average.F90 : wrong call to setv
    could cause an out-of-bound error

                                 * * * * *
```
