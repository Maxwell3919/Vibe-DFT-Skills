# Quantum ESPRESSO release notes — Fixed in 4.3.2 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `38e662d26e5af490441a793ad9e1364f33d6b4cf827992b8a40003eb97936469`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Fixed in 4.3.2 version:

  * Bugfix for pw2casino: total energies should now agree with pwscf total
    energies for any number of nodes/k-points, also for hybrid functionals. 
    Note: bwfn files produced before and after this patch will differ!
  * Funny results in the last step of variable-cell optimization,
    due to bad symmetrization in presence of fractional translations
  * OpenMP crash with PAW
  * Removed lines in iotk that confused some preprocessors
  * More glitches with new xc functionals, compatibility with 
    previous cases: HF, OEP, PZ
  * Variable-cell optimization at fixed volume broke hexagonal symmetry
  * NEB: possible problem in parallel execution (if command-line arguments
    are not available to all processors) avoided by broadcasting arguments
  * PWGui documentation updated to reflect cvs to svn switch
  * Some formats increased to fit printout of large cells
  * PW: the cell volume omega must be positive definite even when the 
    lattice vectors form a left-handed set
  * PW: a bad initialization (of becsum) in the paw spin/orbit case 
    made the convergence more difficult
  * PW: couldn't read any longer data files written by previous versions
  * PHonon: problem with the D_4h group when the matrices of the group 
    are not in the same order as in the routine cubicsym
  * Yet another LDA+CPU+U fix: forces were wrong in spin-polarized case 
  * PW was not stopping anymore when two inconsistent dft were given
  * atomic: default for non-local correlation is set to "   " AND upf%dft 
    is trimmed before being written by write_upf_v2.f90. Therefore older 
    versions of pw will still work if no vdW is present
  * inlc label for vdw-df is set as VDW1, consistently with the comment and 
    needed to avoid matching conflict with VDW2

                               * * * * *
```
